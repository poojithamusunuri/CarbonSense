# API smoke-test checklist

1. Start the backend and open `http://127.0.0.1:8000/docs`.
2. Check `GET /api/v1/health`.
3. Submit a test row to `POST /api/v1/readings`.
4. Check `GET /api/v1/summary`, `/api/v1/analytics/forensics`, `/api/v1/analytics/opportunities`, `/api/v1/analytics/carbon`, `/api/v1/ml/status`, and `/api/v1/ml/anomalies`.
5. Submit a comparable before/after intervention to `POST /api/v1/interventions`; include `duration_minutes` to estimate energy and CO₂e change from the power difference, or provide before/after energy values.
6. Open the dashboard and confirm the stored test row appears. Remove the local SQLite database before final measured trials if you want a clean log.

Test rows are for checking software plumbing only. They are not experimental evidence.
