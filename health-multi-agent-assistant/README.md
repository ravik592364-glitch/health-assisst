# Multilingual AI Health Assistant — Multi-Agent + Doctor-in-the-Loop

A portfolio-ready starter project for a healthcare assistant supporting English, Telugu and Hindi.

## Important safety design
The AI does not independently prescribe medicines. It collects patient information, performs structured analysis, retrieves reference information, checks safety flags, and prepares a summary. A licensed doctor reviews the case and enters/approves the final medicine, dosage, frequency and duration.

This repository contains demo medical-reference data only. Do not use it as a clinical decision system.

## Stack
- Frontend: React + Vite
- Backend: FastAPI
- Agent orchestration: LangGraph-compatible architecture
- LLM integration: optional Gemini API
- Database: SQLite for demo
- Languages: English / Telugu / Hindi

## Run backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Optional Gemini:
```bash
set GEMINI_API_KEY=your_key
```
or PowerShell:
```powershell
$env:GEMINI_API_KEY="your_key"
```

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite, usually http://localhost:5173.

## Demo
1. Enter patient information and symptoms.
2. Select English, Telugu or Hindi.
3. Submit for AI-assisted case preparation.
4. Open the doctor review screen.
5. The doctor enters the final recommendation and approves it.
6. The patient receives the doctor-approved response in the selected language.

## Production notes
Before any real-world deployment, add authentication, role-based access, encrypted data storage, audit logs, consent, clinician verification, validated medical sources, security controls, and applicable healthcare/privacy compliance.
