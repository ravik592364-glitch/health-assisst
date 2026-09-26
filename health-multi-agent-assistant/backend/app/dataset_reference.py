import csv
import os
import re
from functools import lru_cache


DATASET_PATH = os.getenv(
    "HEALTH_DATASET_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "health_assistant_10000_dataset.csv"),
)
MEDICINE_DATASET_PATH = os.getenv(
    "MEDICINE_DATASET_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "health_assistant_500_disease_medicine_dataset.csv"),
)
STOP_WORDS = {"a", "an", "and", "for", "in", "is", "no", "of", "or", "the", "to", "with"}


def _tokens(value):
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (value or "").casefold())
        if len(token) > 2 and token not in STOP_WORDS
    }


@lru_cache(maxsize=1)
def load_dataset():
    if not os.path.exists(DATASET_PATH):
        return []
    with open(DATASET_PATH, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def dataset_status():
    rows = load_dataset()
    return {
        "available": bool(rows),
        "path": DATASET_PATH,
        "rows": len(rows),
        "fields": list(rows[0].keys()) if rows else [],
    }


def find_dataset_references(symptoms, limit=5):
    query_tokens = _tokens(symptoms)
    if not query_tokens:
        return []
    scored = []
    for row in load_dataset():
        row_tokens = _tokens(row.get("symptoms", ""))
        overlap = query_tokens.intersection(row_tokens)
        if overlap:
            scored.append((len(overlap), row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "patient_id": row.get("patient_id"),
            "symptoms": row.get("symptoms"),
            "duration_days": row.get("duration_days"),
            "severity": row.get("severity"),
            "possible_condition": row.get("possible_condition"),
            "recommended_action": row.get("recommended_action"),
            "emergency": row.get("emergency"),
            "match_terms": sorted(_tokens(row.get("symptoms", "")).intersection(query_tokens)),
        }
        for _, row in scored[:limit]
    ]


@lru_cache(maxsize=1)
def load_medicine_dataset():
    if not os.path.exists(MEDICINE_DATASET_PATH):
        return []
    with open(MEDICINE_DATASET_PATH, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def find_medicine_references(symptoms, conditions=None, limit=10):
    query_tokens = _tokens(symptoms)
    condition_tokens = _tokens(" ".join(conditions or []))
    scored = []
    for row in load_medicine_dataset():
        row_tokens = _tokens(f"{row.get('disease', '')} {row.get('symptoms', '')}")
        overlap = query_tokens.intersection(row_tokens)
        condition_overlap = condition_tokens.intersection(_tokens(row.get("disease", "")))
        score = len(overlap) + (2 * len(condition_overlap))
        if score:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "disease_id": row.get("disease_id"),
            "disease": row.get("disease"),
            "symptoms": row.get("symptoms"),
            "medicine_or_tablet": row.get("medicine_or_tablet"),
            "dosage": row.get("dosage"),
            "route": row.get("route"),
            "treatment_note": row.get("treatment_note"),
            "dataset_type": row.get("dataset_type"),
            "medical_disclaimer": row.get("medical_disclaimer"),
        }
        for _, row in scored[:limit]
    ]
