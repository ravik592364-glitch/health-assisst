import os, re
from .data import COMMON_MEDICINES, CONDITIONS, RED_FLAGS
from .dataset_reference import find_dataset_references, find_medicine_references

TRANSLATIONS = {
    "en": {
        "emergency": "Some symptoms may require urgent medical attention. Please seek emergency care now.",
        "summary": "Your information has been prepared for doctor review.",
        "doctor": "A doctor must review the case and make the final diagnosis and medication recommendation."
    },
    "te": {
        "emergency": "కొన్ని లక్షణాలకు అత్యవసర వైద్య సహాయం అవసరం కావచ్చు. వెంటనే అత్యవసర వైద్య సేవలను సంప్రదించండి.",
        "summary": "మీ వివరాలను డాక్టర్ సమీక్ష కోసం సిద్ధం చేశాము.",
        "doctor": "డాక్టర్ కేసును సమీక్షించి తుది నిర్ధారణ మరియు మందుల సిఫార్సు చేయాలి."
    },
    "hi": {
        "emergency": "कुछ लक्षणों में तुरंत चिकित्सा सहायता की आवश्यकता हो सकती है। कृपया तुरंत आपातकालीन चिकित्सा सेवा लें।",
        "summary": "आपकी जानकारी डॉक्टर की समीक्षा के लिए तैयार की गई है।",
        "doctor": "डॉक्टर केस की समीक्षा करके अंतिम निदान और दवा की सिफारिश करेंगे।"
    }
}

def detect_red_flags(symptoms: str):
    s = symptoms.casefold()
    return [x for x in RED_FLAGS if x.casefold() in s]

def has_symptom(symptoms: str, aliases):
    normalized = symptoms.casefold()
    return any(alias.casefold() in normalized for alias in aliases)

FEVER_ALIASES = [
    "fever", "high temperature", "temperature", "pyrexia",
    "జ్వరం", "తీవ్ర జ్వరం", "బాడీ హీట్",
    "बुखार", "तेज बुखार", "शरीर में गर्मी",
]

FEVER_RED_FLAG_ALIASES = [
    "confusion", "confused", "stiff neck", "neck stiffness",
    "difficulty breathing", "shortness of breath", "severe dehydration",
    "persistent vomiting", "कन्फ्यूजन", "गर्दन अकड़ना",
    "శ్వాస తీసుకోవడంలో ఇబ్బంది", "మెడ బిగుసుకుపోవడం",
]

SYMPTOM_ALIASES = {
    "fever": ["fever", "high fever", "high temperature", "pyrexia", "జ్వరం", "बुखार"],
    "chills": ["chills", "shivering", "శీతల వణుకు", "ठंड लगना"],
    "fatigue": ["fatigue", "tiredness", "weakness", "మగత", "అలసట", "थकान", "कमजोरी"],
    "dizziness": ["dizziness", "lightheaded", "తల తిరగడం", "चक्कर"],
    "fainting": ["fainting", "fainted", "loss of consciousness", "స్పృహ కోల్పోవడం", "बेहोशी"],
    "headache": ["headache", "head ache", "headche", "headche", "తలనొప్పి", "सिरदर्द", "सिर दर्द"],
    "chest pain": ["chest pain", "chest pressure", "ఛాతీ నొప్పి", "सीने में दर्द"],
    "abdominal pain": ["abdominal pain", "stomach pain", "కడుపు నొప్పి", "पेट दर्द"],
    "back pain": ["back pain", "వెన్ను నొప్పి", "कमर दर्द"],
    "joint pain": ["joint pain", "కీళ్ల నొప్పి", "కీళ్ల నొప్పులు", "जोड़ों का दर्द"],
    "muscle pain": ["muscle pain", "body pain", "body pains", "బాడీ పెయిన్స్", "शरीर में दर्द"],
    "throat pain": ["throat pain", "sore throat", "గొంతు నొప్పి", "గొంతు మంట", "गले में दर्द", "गले में खराश"],
    "cough": ["cough", "dry cough", "wet cough", "దగ్గు", "खांसी"],
    "shortness of breath": ["shortness of breath", "difficulty breathing", "శ్వాస తీసుకోవడంలో ఇబ్బంది", "सांस लेने में कठिनाई"],
    "wheezing": ["wheezing", "గురక శ్వాస", "सीटी जैसी सांस"],
    "nausea": ["nausea", "వికారం", "मतली"],
    "vomiting": ["vomiting", "వాంతులు", "उल्टी"],
    "diarrhea": ["diarrhea", "loose stools", "విరేచనాలు", "दस्त"],
    "rash": ["rash", "skin rash", "దద్దుర్లు", "चकत्ते"],
    "itching": ["itching", "దురద", "खुजली"],
    "burning urination": ["burning urination", "painful urination", "మూత్రం పోసేటప్పుడు మంట", "पेशाब में जलन"],
    "confusion": ["confusion", "confused", "గందరగోళం", "भ्रम"],
}

TREATMENT_REFERENCES = {
    "Common Cold": "Paracetamol for fever/pain; antihistamines or decongestants only when clinically appropriate.",
    "Influenza (Flu)": "Oseltamivir for appropriate patients; otherwise supportive treatment.",
    "Pneumonia": "Antibiotics only when bacterial and prescribed by a clinician; supportive treatment.",
    "Bronchitis": "Usually supportive care; bronchodilator only if clinically indicated.",
    "COVID-19": "Supportive treatment; selected high-risk patients may receive antiviral therapy.",
    "Dengue": "Supportive treatment; paracetamol may be considered by a clinician. Avoid aspirin or ibuprofen unless specifically directed.",
    "Malaria": "Antimalarial regimen depends on species, resistance, and severity; clinician assessment is required.",
    "Typhoid": "Antibiotic selected by a clinician based on local resistance and testing.",
}

STRUCTURED_TREATMENT_OPTIONS = {
    "Hypertension": {
        "condition": "Hypertension",
        "treatment_options": [
            {"medicine": "Amlodipine", "type": "Calcium-channel blocker"},
            {"medicine": "Losartan", "type": "ARB"},
        ],
        "doctor_required": True,
    },
}

def find_reference_conditions(symptoms: str):
    s = symptoms.casefold()
    hits = []
    keywords = {
        "fever": ["Influenza (Flu)", "Dengue", "Malaria", "Typhoid", "COVID-19"],
        "cough": ["Common Cold", "Influenza (Flu)", "Asthma", "Bronchitis", "Pneumonia", "COVID-19"],
        "headache": ["Migraine"],
        "joint pain": ["Arthritis", "Gout"],
        "throat pain": ["Common Cold", "Influenza (Flu)", "Bronchitis", "Pneumonia", "COVID-19"],
        "sore throat": ["Common Cold", "Influenza (Flu)", "Bronchitis", "Pneumonia", "COVID-19"],
        "acid reflux": ["GERD / Acid Reflux"],
        "heartburn": ["GERD / Acid Reflux"],
        "itching": ["Eczema", "Dermatitis", "Fungal Skin Infection"],
        "burning urination": ["Urinary Tract Infection (UTI)"],
        "seizure": ["Epilepsy"],
        "urinary infection": ["Urinary Tract Infection (UTI)"],
        "urine infection": ["Urinary Tract Infection (UTI)"],
        "uti": ["Urinary Tract Infection (UTI)"],
    }
    aliases = {
        "fever": ["జ్వరం", "బుఖార్", "बुखार"],
        "cough": ["దగ్గు", "खांसी"],
        "headache": ["head ache", "headche", "తలనొప్పి", "सिरदर्द", "सिर दर्द"],
        "joint pain": ["కీళ్ల నొప్పి", "కీళ్ల నొప్పులు", "जोड़ों का दर्द"],
        "throat pain": ["గొంతు నొప్పి", "గొంతు మంట", "गले में दर्द", "गले का दर्द"],
        "sore throat": ["గొంతు నొప్పి", "గొంతు మంట", "गले में खराश"],
        "itching": ["దురద", "खुजली"],
        "burning urination": ["మూత్రం పోసేటప్పుడు మంట", "पेशाब में जलन"],
    }
    for key, names in keywords.items():
        if has_symptom(s, [key, *aliases.get(key, [])]):
            hits.extend(names)
    if has_symptom(s, FEVER_ALIASES):
        hits.extend(keywords["fever"])
    return sorted(set(hits))

def detect_symptoms(symptoms: str):
    return sorted(name for name, aliases in SYMPTOM_ALIASES.items() if has_symptom(symptoms, aliases))

def medicine_information_for_case(symptoms: str, allergies: str, current_medicines: str):
    detected = detect_symptoms(symptoms)
    area_by_symptom = {
        "muscle pain": "Muscle pain",
        "joint pain": "Joint pain",
        "fever": "Fever / pain",
        "headache": "Headache",
        "itching": "Skin allergy / itching",
        "rash": "Skin allergy / itching",
    }
    areas = {area_by_symptom.get(item, item) for item in detected}
    if has_symptom(symptoms, ["fever", "high temperature", "జ్వరం", "बुखार"]):
        areas.add("Fever / pain")
    if has_symptom(
        f"{symptoms} {allergies}",
        ["rash", "skin rash", "దద్దుర్లు", "चकत्ते", "itching", "దురద", "खुजली"],
    ):
        areas.add("Skin allergy / itching")
    if has_symptom(symptoms, ["headache", "head ache", "తలనొప్పి", "सिरदर्द"]):
        areas.add("Headache")
    items = [item for item in COMMON_MEDICINES if item["area"] in areas]
    safety_checks = [
        "Check allergies, age, pregnancy status when relevant, medical conditions, and current medicines before prescribing.",
        "Do not duplicate paracetamol-containing products when the patient is already taking a paracetamol product.",
    ]
    if allergies.strip():
        safety_checks.append(f"Reported allergy information requires review before any medicine is selected: {allergies.strip()}.")
    if current_medicines.strip():
        safety_checks.append(f"Check for interactions with current medicines: {current_medicines.strip()}.")
    return {"items": items, "safety_checks": safety_checks}

def run_health_workflow(case):
    flags = detect_red_flags(case["symptoms"])
    if has_symptom(case["symptoms"], FEVER_ALIASES) and has_symptom(case["symptoms"], FEVER_RED_FLAG_ALIASES):
        flags.append("fever with potentially serious warning symptoms")
    flags = sorted(set(flags))
    possible = find_reference_conditions(case["symptoms"])
    detected = detect_symptoms(case["symptoms"])
    treatment_references = [
        {"condition": condition, "examples": TREATMENT_REFERENCES[condition]}
        for condition in possible
        if condition in TREATMENT_REFERENCES
    ]
    medicine_information = medicine_information_for_case(
        case["symptoms"],
        case.get("allergies", ""),
        case.get("current_medicines", ""),
    )
    dataset_references = find_dataset_references(case["symptoms"])
    medicine_references = find_medicine_references(case["symptoms"], possible)
    structured_treatments = [
        STRUCTURED_TREATMENT_OPTIONS[condition]
        for condition in possible
        if condition in STRUCTURED_TREATMENT_OPTIONS
    ]
    lang = case.get("language", "en")
    t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    doctor_note = t["doctor"]
    if has_symptom(case["symptoms"], FEVER_ALIASES):
        doctor_note += " Fever cases should be reviewed with measured temperature, onset and duration, hydration status, associated symptoms, travel/exposure history, and relevant medical history."
    if has_symptom(case["symptoms"], ["muscle pain", "body pain", "body pains", "शरीर में दर्द", "బాడీ పెయిన్స్"]):
        doctor_note += " For body pain, a clinician may consider an appropriate tablet only after reviewing the reported rash, allergies, current medicines, and contraindications; do not duplicate paracetamol-containing products."

    return {
        "workflow": ["language_agent", "intake_agent", "triage_agent", "medical_rag_agent", "doctor_review"],
        "triage": "urgent" if flags else "routine_review",
        "red_flags": flags,
        "detected_symptoms": detected,
        "possible_reference_conditions": possible,
        "treatment_references": treatment_references,
        "medicine_information": medicine_information,
        "dataset_references": dataset_references,
        "dataset_notice": "Dataset matches are historical reference examples for clinician review only. They are not a diagnosis, prescription, or substitute for vital-sign assessment.",
        "medicine_references": medicine_references,
        "medicine_dataset_notice": "Disease and tablet matches are synthetic educational reference data for a licensed doctor. They must not be treated as an automatic prescription. Verify diagnosis, allergies, age, pregnancy status when relevant, current medicines, contraindications, and local guidance.",
        "structured_treatments": structured_treatments,
        "patient_summary": {
            "name": case["name"],
            "age": case["age"],
            "symptoms": case["symptoms"],
            "duration": case.get("duration", ""),
            "allergies": case.get("allergies", ""),
            "current_medicines": case.get("current_medicines", ""),
            "medical_history": case.get("medical_history", ""),
        },
        "language": lang,
        "message": t["emergency"] if flags else t["summary"],
        "doctor_note": doctor_note,
        "medicine_policy": "No autonomous prescription. Final medicine, dose, frequency and duration are entered and approved by the doctor."
    }
