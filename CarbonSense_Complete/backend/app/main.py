from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pathlib import Path
from datetime import datetime, timezone
import sqlite3, csv, io, os, statistics, json
from collections import defaultdict
from math import isfinite

DB_PATH = Path(os.getenv("CARBONSENSE_DB", str(Path(__file__).resolve().parents[1] / "carbonsense.sqlite")))
app = FastAPI(title="CarbonSense API", version="2.0.0",
              description="CarbonSense: IoT energy monitoring, load identification, anomaly investigation, carbon estimates, and Action-Measure-Verify.")
GRID_FACTOR_KG_PER_KWH = float(os.getenv("CARBONSENSE_GRID_FACTOR_KG_PER_KWH", "0.716"))
GRID_FACTOR_NOTE = os.getenv("CARBONSENSE_GRID_FACTOR_NOTE", "Configurable example factor; verify the latest official regional factor before reporting results.")
MODEL_DIR = Path(os.getenv("CARBONSENSE_MODEL_DIR", str(Path(__file__).resolve().parents[2] / "ml" / "models" / "college_prototype")))
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS readings (
          id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
          device_id TEXT NOT NULL, load_label TEXT NOT NULL,
          voltage_v REAL NOT NULL, current_ma REAL NOT NULL, power_mw REAL NOT NULL,
          energy_wh REAL NOT NULL, data_origin TEXT NOT NULL DEFAULT 'hardware',
          run_id TEXT, condition_label TEXT, notes TEXT, temperature_c REAL, duty_cycle_pct REAL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS interventions (
          id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
          title TEXT NOT NULL, before_power_mw REAL, after_power_mw REAL,
          notes TEXT, data_origin TEXT NOT NULL DEFAULT 'user-entered',
          before_energy_wh REAL, after_energy_wh REAL, duration_minutes REAL,
          energy_saved_wh REAL, co2e_saved_kg_estimate REAL, reduction_percent REAL)""")
        # Safe additive migrations for databases created by earlier project versions.
        reading_cols={r[1] for r in con.execute("PRAGMA table_info(readings)")}
        for name, sqltype in [("temperature_c","REAL"),("duty_cycle_pct","REAL")]:
            if name not in reading_cols: con.execute(f"ALTER TABLE readings ADD COLUMN {name} {sqltype}")
        intervention_cols={r[1] for r in con.execute("PRAGMA table_info(interventions)")}
        for name, sqltype in [("before_energy_wh","REAL"),("after_energy_wh","REAL"),("duration_minutes","REAL"),("energy_saved_wh","REAL"),("co2e_saved_kg_estimate","REAL"),("reduction_percent","REAL")]:
            if name not in intervention_cols: con.execute(f"ALTER TABLE interventions ADD COLUMN {name} {sqltype}")
init_db()

class Reading(BaseModel):
    device_id: str = Field(min_length=1, max_length=100)
    load_label: str = Field(default="unknown", max_length=50)
    voltage_v: float
    current_ma: float
    power_mw: float
    energy_wh: float = 0
    data_origin: str = "hardware"
    run_id: str | None = None
    condition_label: str | None = None
    notes: str | None = None
    temperature_c: float | None = None
    duty_cycle_pct: float | None = None

class Intervention(BaseModel):
    title: str
    before_power_mw: float | None = None
    after_power_mw: float | None = None
    before_energy_wh: float | None = None
    after_energy_wh: float | None = None
    duration_minutes: float | None = None
    notes: str | None = None
    data_origin: str = "user-entered"

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "CarbonSense API", "database": str(DB_PATH),
            "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/api/v1/readings")
def create_reading(r: Reading):
    timestamp = datetime.now(timezone.utc).isoformat()
    with db() as con:
        cur = con.execute("""INSERT INTO readings
          (timestamp,device_id,load_label,voltage_v,current_ma,power_mw,energy_wh,data_origin,run_id,condition_label,notes,temperature_c,duty_cycle_pct)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (timestamp,r.device_id,r.load_label,r.voltage_v,r.current_ma,r.power_mw,r.energy_wh,
           r.data_origin,r.run_id,r.condition_label,r.notes,r.temperature_c,r.duty_cycle_pct))
        rid = cur.lastrowid
    return {"accepted": True, "id": rid, "timestamp": timestamp}

@app.get("/api/v1/readings")
def get_readings(limit: int = 500, device_id: str | None = None, load_label: str | None = None):
    limit = max(1, min(limit, 5000))
    q = "SELECT * FROM readings"
    where, params = [], []
    if device_id: where.append("device_id=?"); params.append(device_id)
    if load_label: where.append("load_label=?"); params.append(load_label)
    if where: q += " WHERE " + " AND ".join(where)
    q += " ORDER BY id DESC LIMIT ?"; params.append(limit)
    with db() as con: rows = [dict(r) for r in con.execute(q, params).fetchall()]
    return {"count": len(rows), "readings": list(reversed(rows))}

@app.get("/api/v1/summary")
def summary():
    with db() as con:
        n = con.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
        row = con.execute("""SELECT AVG(voltage_v) avgv, AVG(current_ma) avgi,
          AVG(power_mw) avgp, MAX(power_mw) maxp, MAX(timestamp) latest FROM readings""").fetchone()
        loads = [dict(r) for r in con.execute("""SELECT load_label,COUNT(*) samples,
          AVG(power_mw) avg_power_mw,AVG(current_ma) avg_current_ma
          FROM readings GROUP BY load_label ORDER BY load_label""").fetchall()]
        origins = [dict(r) for r in con.execute("SELECT data_origin,COUNT(*) count FROM readings GROUP BY data_origin").fetchall()]
    return {"samples": n, "avg_voltage_v": row["avgv"], "avg_current_ma": row["avgi"],
            "avg_power_mw": row["avgp"], "max_power_mw": row["maxp"],
            "latest_timestamp": row["latest"], "loads": loads, "origins": origins}

@app.get("/api/v1/alerts")
def alerts():
    with db() as con:
        latest = con.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 1").fetchone()
    if not latest: return {"alerts": [], "message": "No readings yet"}
    r = dict(latest); out = []
    if r["voltage_v"] <= 0.1: out.append({"severity":"warning","title":"Near-zero voltage",
      "message":"Check sensor wiring, load supply and INA219 VIN+/VIN- path."})
    if r["current_ma"] < -0.5: out.append({"severity":"warning","title":"Negative current",
      "message":"Check current direction, sensor offset and wiring."})
    if r["power_mw"] < 0: out.append({"severity":"warning","title":"Negative power",
      "message":"Check sign convention and measurement path."})
    return {"alerts": out, "latest": r}

@app.post("/api/v1/interventions")
def create_intervention(i: Intervention):
    ts = datetime.now(timezone.utc).isoformat()
    reduction = None; energy_saved_wh = None; co2e_saved_kg = None
    if i.before_energy_wh is not None and i.after_energy_wh is not None:
        energy_saved_wh = i.before_energy_wh - i.after_energy_wh
    elif i.duration_minutes and i.duration_minutes > 0 and i.before_power_mw is not None and i.after_power_mw is not None:
        energy_saved_wh = ((i.before_power_mw - i.after_power_mw) / 1000.0) * (i.duration_minutes / 60.0)
    if i.before_power_mw is not None and i.before_power_mw > 0 and i.after_power_mw is not None:
        reduction = 100 * (i.before_power_mw - i.after_power_mw) / i.before_power_mw
    elif i.before_energy_wh is not None and i.before_energy_wh > 0 and i.after_energy_wh is not None:
        reduction = 100 * (i.before_energy_wh - i.after_energy_wh) / i.before_energy_wh
    if energy_saved_wh is not None:
        co2e_saved_kg = (energy_saved_wh / 1000.0) * GRID_FACTOR_KG_PER_KWH
    with db() as con:
        cur = con.execute("""INSERT INTO interventions(timestamp,title,before_power_mw,after_power_mw,notes,data_origin,
          before_energy_wh,after_energy_wh,duration_minutes,energy_saved_wh,co2e_saved_kg_estimate,reduction_percent)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(ts,i.title,i.before_power_mw,i.after_power_mw,i.notes,i.data_origin,
          i.before_energy_wh,i.after_energy_wh,i.duration_minutes,energy_saved_wh,co2e_saved_kg,reduction))
    return {"id":cur.lastrowid,"timestamp":ts,"reduction_percent":reduction,
            "energy_saved_wh":energy_saved_wh,"co2e_saved_kg_estimate":co2e_saved_kg,
            "grid_factor_kg_per_kwh":GRID_FACTOR_KG_PER_KWH,"factor_note":GRID_FACTOR_NOTE,
            "verification_note":"A valid comparison requires comparable measurement durations and operating conditions."}

@app.get("/api/v1/interventions")
def list_interventions():
    with db() as con: rows=[dict(r) for r in con.execute("SELECT * FROM interventions ORDER BY id DESC").fetchall()]
    return {"count":len(rows),"interventions":rows}

@app.get("/api/v1/analytics/forensics")
def forensics(limit: int = 1000):
    """Explain recent changes against per-load baselines; anomaly means investigate, not proven waste."""
    with db() as con:
        rows = [dict(r) for r in con.execute("SELECT * FROM readings ORDER BY id DESC LIMIT ?", (max(10,min(limit,5000)),)).fetchall()]
    rows.reverse()
    by_load = defaultdict(list)
    for row in rows: by_load[row["load_label"]].append(row)
    events=[]; stories=[]
    for label, group in by_load.items():
        powers=[float(x["power_mw"]) for x in group if x["power_mw"] is not None and isfinite(float(x["power_mw"]))]
        if not powers: continue
        baseline=powers[:-min(10,len(powers))] if len(powers)>10 else powers
        mean=statistics.mean(baseline) if baseline else statistics.mean(powers)
        sd=statistics.pstdev(baseline) if len(baseline)>1 else 0.0
        latest=group[-1]; power=float(latest["power_mw"])
        threshold=max(mean*1.5, mean+3*sd, mean+1.0)
        if power > threshold and len(powers)>=5:
            events.append({"load_label":label,"severity":"warning","title":"Power above recent baseline",
                "observed_power_mw":power,"baseline_power_mw":mean,"change_percent":(power-mean)/mean*100 if mean>0 else None,
                "timestamp":latest["timestamp"],"explanation":f"Latest power is above the recent {label} baseline. Check operating state and repeat the measurement before calling it waste."})
        stories.append({"load_label":label,"samples":len(powers),"baseline_power_mw":mean,"latest_power_mw":power,
            "change_percent":(power-mean)/mean*100 if mean>0 else None,
            "story": (f"{label} is running above its recent baseline; inspect the load state and repeat the test." if power>threshold and len(powers)>=5 else f"{label} is being tracked against its observed baseline.")})
    return {"events":events,"stories":stories,"method":"Interpretable per-load recent baseline; minimum five samples for alerting.",
            "caution":"An anomaly is a prompt to investigate, not proof of energy waste or equipment fault."}

@app.get("/api/v1/analytics/opportunities")
def opportunities():
    with db() as con:
        loads=[dict(r) for r in con.execute("SELECT load_label,COUNT(*) samples,AVG(power_mw) avg_power_mw,MAX(power_mw) max_power_mw FROM readings GROUP BY load_label").fetchall()]
    out=[]
    for x in loads:
        p=max(0.0,float(x["avg_power_mw"] or 0))
        # Ranking is a transparent heuristic, not an ML prediction.
        out.append({"load_label":x["load_label"],"samples":x["samples"],"average_power_mw":p,
          "priority_score":round(p*min(1.0,x["samples"]/20),3),"suggested_action":"Compare an equivalent-duration baseline with a controlled lower-power/off state.",
          "basis":"Measured mean power × sample-confidence factor; review feasibility and service needs before acting."})
    return {"opportunities":sorted(out,key=lambda z:z["priority_score"],reverse=True),"ranking_method":"Transparent measured-power heuristic; not a guarantee of savings."}

@app.get("/api/v1/analytics/carbon")
def carbon_summary():
    with db() as con:
        rows=[dict(r) for r in con.execute("SELECT timestamp,power_mw,energy_wh FROM readings WHERE data_origin='hardware' ORDER BY id").fetchall()]
    # Integrate measured power over elapsed timestamp intervals. Do not sum cumulative energy counters.
    energy_wh=0.0
    from datetime import timedelta
    for prev,cur in zip(rows,rows[1:]):
        try:
            t0=datetime.fromisoformat(prev["timestamp"].replace("Z","+00:00")); t1=datetime.fromisoformat(cur["timestamp"].replace("Z","+00:00"))
            hours=max(0.0,(t1-t0).total_seconds()/3600.0)
            p0=max(0.0,float(prev["power_mw"] or 0)); p1=max(0.0,float(cur["power_mw"] or 0))
            energy_wh += ((p0+p1)/2.0/1000.0)*hours
        except (ValueError,TypeError):
            continue
    return {"hardware_samples":len(rows),"integrated_energy_wh_estimate":energy_wh,
      "estimated_co2e_kg":energy_wh/1000*GRID_FACTOR_KG_PER_KWH,
      "grid_factor_kg_per_kwh":GRID_FACTOR_KG_PER_KWH,"factor_note":GRID_FACTOR_NOTE,
      "scope":"Only hardware-tagged readings are included. Energy is trapezoid-integrated from timestamps and power; sparse samples, device gaps, sensor calibration, and the configurable emissions factor affect accuracy."}

@app.get("/api/v1/ml/status")
def ml_status():
    classifier=MODEL_DIR/"load_classifier.joblib"
    anomaly=MODEL_DIR/"anomaly_detector.joblib"
    evaluation=MODEL_DIR/"evaluation.json"
    meta=None
    if evaluation.exists():
        try: meta=json.loads(evaluation.read_text())
        except Exception: meta=None
    return {"classifier_available":classifier.exists(),"anomaly_model_available":anomaly.exists(),
      "evaluation_available":evaluation.exists(),"model_directory":str(MODEL_DIR),"evaluation":meta,
      "message":"Train models with ml/train_evaluate.py. Until artifacts exist, dashboard forensics uses transparent baseline rules."}

@app.post("/api/v1/ml/predict")
def ml_predict(r: Reading):
    model_path=MODEL_DIR/"load_classifier.joblib"
    if not model_path.exists():
        raise HTTPException(status_code=503, detail="Classifier not trained yet. Run the ML training command in README.md first.")
    try:
        import joblib, pandas as pd
        model=joblib.load(model_path)
        frame=pd.DataFrame([{k:getattr(r,k,None) for k in ["voltage_v","current_ma","power_mw","energy_wh","temperature_c","duty_cycle_pct"]}])
        # The live Reading schema has no temperature/duty-cycle fields; mark missing and let the trained pipeline impute.
        prediction=str(model.predict(frame)[0])
        probs=model.predict_proba(frame)[0].tolist() if hasattr(model,"predict_proba") else []
        classes=model.classes_.tolist() if hasattr(model,"classes_") else []
        return {"predicted_load":prediction,"confidence":max(probs) if probs else None,
          "class_probabilities":dict(zip(classes,probs)),"model_scope":"Only valid for the dataset/study stage used to train this model.",
          "warning":"Prediction is not a safety assessment and unfamiliar loads may be misclassified."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")

@app.get("/api/v1/ml/anomalies")
def ml_anomalies(limit: int = 200):
    model_path=MODEL_DIR/"anomaly_detector.joblib"
    if not model_path.exists():
        return {"available":False,"anomalies":[],"message":"Train the anomaly detector with ml/train_evaluate.py; baseline-rule forensics remains available."}
    with db() as con:
        rows=[dict(r) for r in con.execute("SELECT * FROM readings ORDER BY id DESC LIMIT ?",(max(1,min(limit,1000)),)).fetchall()]
    rows.reverse()
    if not rows: return {"available":True,"anomalies":[],"message":"No readings stored."}
    try:
        import joblib, pandas as pd
        model=joblib.load(model_path)
        features=["voltage_v","current_ma","power_mw","energy_wh","temperature_c","duty_cycle_pct"]
        frame=pd.DataFrame([{k:r.get(k) for k in features} for r in rows])
        labels=model.predict(frame)
        result=[]
        for row,label in zip(rows,labels):
            if int(label)==-1:
                result.append({"timestamp":row["timestamp"],"load_label":row["load_label"],"power_mw":row["power_mw"],
                    "data_origin":row["data_origin"],"severity":"investigate","explanation":"ML model flagged this measurement as unusual relative to its training distribution; inspect context before drawing conclusions."})
        return {"available":True,"anomalies":result,"method":"IsolationForest trained on the selected dataset","caution":"A flagged point is not proof of energy waste. Validate against actual hardware data."}
    except Exception as exc:
        raise HTTPException(status_code=500,detail=f"Anomaly inference failed: {exc}")

@app.get("/api/v1/export.csv")
def export_csv():
    with db() as con: rows=[dict(r) for r in con.execute("SELECT * FROM readings ORDER BY id").fetchall()]
    fields=["id","timestamp","device_id","load_label","voltage_v","current_ma","power_mw","energy_wh","data_origin","run_id","condition_label","notes"]
    out=io.StringIO(); w=csv.DictWriter(out,fieldnames=fields); w.writeheader(); w.writerows(rows)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition":"attachment; filename=carbonsense_readings.csv"})
