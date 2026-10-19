# Project layout
- `firmware/`: ESP32 Arduino sketch and local configuration template.
- `backend/`: FastAPI ingestion, SQLite persistence, summary, alert and CSV APIs.
- `dashboard/`: browser UI that polls the API every five seconds and renders only API-returned values.
- `data/college_prototype/`: synthetic development dataset representing the small DC-load prototype.
- `data/real_world_scenario/`: synthetic scenario dataset with illustrative larger-system conditions. It is not field data.
- `data/schema.md`: field definitions and capture procedure.
- `ml/`: group-aware training/evaluation script.
- `docs/`: build, hardware, ML, scaling and validation plans.
