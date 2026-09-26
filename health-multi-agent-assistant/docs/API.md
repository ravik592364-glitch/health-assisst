# API

GET `/api/conditions`
- Returns demo condition/reference records.

POST `/api/analyze`
- Accepts patient intake and returns a structured case for doctor review.

POST `/api/doctor/recommend`
- Records a doctor recommendation payload in the demo flow.

Example analyze body:
```json
{
  "name":"Ravi",
  "age":25,
  "language":"te",
  "symptoms":"fever and cough",
  "duration":"2 days",
  "allergies":"",
  "current_medicines":"",
  "medical_history":""
}
```
