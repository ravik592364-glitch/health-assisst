import os
import tempfile
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from .agents import STRUCTURED_TREATMENT_OPTIONS, run_health_workflow
from .data import COMMON_MEDICINES, CONDITIONS
from .storage import initialize_database, list_cases, save_case, save_recommendation
from .dataset_reference import dataset_status, find_dataset_references, find_medicine_references, load_medicine_dataset

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    return _whisper_model

app = FastAPI(title="Multilingual AI Health Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
initialize_database()

class PatientCase(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0, le=120)
    language: str = "en"
    symptoms: str = Field(min_length=1)
    duration: str = ""
    allergies: str = ""
    current_medicines: str = ""
    medical_history: str = ""

class DoctorRecommendation(BaseModel):
    case_id: int | None = None
    assessment: str
    medicine: str
    dosage: str = ""
    frequency: str = ""
    duration: str = ""
    instructions: str = ""

@app.get("/")
def root():
    return {"message": "Multilingual AI Health Assistant API"}

@app.get("/api/conditions")
def conditions():
    return CONDITIONS

@app.get("/api/medicine-information")
def medicine_information():
    return {
        "items": COMMON_MEDICINES,
        "warning": "Educational medicine information for clinician review only. It is not a diagnosis or prescription.",
        "prescription_warning": "Prescription medicines must not be started, stopped, or changed without a licensed clinician.",
    }

@app.get("/api/dataset/status")
def dataset_information():
    return dataset_status()

@app.get("/api/dataset/search")
def dataset_search(symptoms: str):
    return {"matches": find_dataset_references(symptoms, limit=20), **dataset_status()}

@app.get("/api/medicine-dataset")
def medicine_dataset_search(symptoms: str = "", disease: str = ""):
    query = " ".join(value for value in [symptoms, disease] if value)
    return {
        "matches": find_medicine_references(query, [disease] if disease else [], limit=50),
        "rows": len(load_medicine_dataset()),
        "warning": "Educational doctor reference only; not a prescription.",
    }

@app.get("/api/treatment-options")
def treatment_options(condition: str):
    return STRUCTURED_TREATMENT_OPTIONS.get(
        condition,
        {"condition": condition, "treatment_options": [], "doctor_required": True},
    )

@app.post("/api/analyze")
def analyze(case: PatientCase):
    case_data = case.model_dump()
    analysis = run_health_workflow(case_data)
    analysis["case_id"] = save_case(case_data, analysis)
    return analysis

@app.get("/api/cases")
def cases():
    return list_cases()

@app.post("/api/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form("en"),
):
    if language not in {"en", "te", "hi"}:
        language = "en"

    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    contents = await audio.read()
    if not contents:
        return {"text": "", "language": language}

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
            temporary_file.write(contents)
            temporary_path = temporary_file.name

        segments, info = get_whisper_model().transcribe(
            temporary_path,
            language=language,
            beam_size=5,
        )
        text = " ".join(segment.text for segment in segments).strip()
        return {"text": text, "language": info.language}
    finally:
        if temporary_path:
            try:
                os.remove(temporary_path)
            except OSError:
                pass

@app.post("/api/doctor/recommend")
def doctor_recommend(rec: DoctorRecommendation):
    recommendation = rec.model_dump(exclude={"case_id"})
    if rec.case_id is not None and not save_recommendation(rec.case_id, recommendation):
        raise HTTPException(status_code=404, detail="Patient case was not found.")
    return {
        "status": "doctor_reviewed",
        "recommendation": recommendation,
        "safety_note": "Final medication decisions must be made by an appropriately licensed clinician after reviewing the patient."
    }
