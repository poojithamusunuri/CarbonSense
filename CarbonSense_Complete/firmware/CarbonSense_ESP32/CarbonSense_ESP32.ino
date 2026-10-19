#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_INA219.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "config.h"

#define SDA_PIN 21
#define SCL_PIN 22
#define OLED_ADDR 0x3C
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SAMPLE_INTERVAL_MS 2000

Adafruit_INA219 ina219;
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
unsigned long lastSample = 0;
float energyWh = 0.0f;
bool inaReady = false;
bool oledReady = false;

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  unsigned long started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < 20000) {
    delay(500); Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWi-Fi connected");
    Serial.print("ESP32 IP: "); Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWi-Fi not connected; readings will print locally.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(800);
  Wire.begin(SDA_PIN, SCL_PIN);
  inaReady = ina219.begin();
  Serial.println(inaReady ? "INA219 detected" : "ERROR: INA219 not detected");
  oledReady = display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
  if (oledReady) {
    display.clearDisplay(); display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1); display.setCursor(0, 0);
    display.println("CarbonSense"); display.println("Booting..."); display.display();
  } else {
    Serial.println("OLED not detected at 0x3C");
  }
  connectWiFi();
}

void loop() {
  if (millis() - lastSample < SAMPLE_INTERVAL_MS) return;
  unsigned long now = millis();
  float busV = 0, shuntmV = 0, currentmA = 0, powermW = 0;
  if (inaReady) {
    busV = ina219.getBusVoltage_V();
    shuntmV = ina219.getShuntVoltage_mV();
    currentmA = ina219.getCurrent_mA();
    powermW = ina219.getPower_mW();
  }
  float dtHours = (now - lastSample) / 3600000.0f;
  if (lastSample > 0 && powermW > 0) energyWh += (powermW / 1000.0f) * dtHours;
  lastSample = now;

  Serial.printf("V=%.3f,I=%.3f,P=%.3f,E=%.6f,INA219=%s\n",
                busV, currentmA, powermW, energyWh, inaReady ? "OK" : "MISSING");

  if (oledReady) {
    display.clearDisplay(); display.setCursor(0, 0);
    display.println("CarbonSense");
    display.printf("V: %.2f V\n", busV);
    display.printf("I: %.1f mA\n", currentmA);
    display.printf("P: %.1f mW\n", powermW);
    display.printf("WiFi: %s\n", WiFi.status() == WL_CONNECTED ? "connected" : "offline");
    display.display();
  }

  if (WiFi.status() == WL_CONNECTED && inaReady) {
    HTTPClient http;
    String url = String("http://") + API_HOST + ":" + String(API_PORT) + "/api/v1/readings";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    String body = "{";
    body += "\"device_id\":\"" DEVICE_ID "\",";
    body += "\"load_label\":\"" LOAD_LABEL "\",";
    body += "\"voltage_v\":" + String(busV, 4) + ",";
    body += "\"current_ma\":" + String(currentmA, 4) + ",";
    body += "\"power_mw\":" + String(powermW, 4) + ",";
    body += "\"energy_wh\":" + String(energyWh, 7) + ",";
    body += "\"data_origin\":\"hardware\"}";
    int code = http.POST(body);
    Serial.printf("POST status: %d\n", code);
    http.end();
  }
}
