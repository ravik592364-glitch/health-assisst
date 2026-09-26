import json
import os
import sqlite3
from datetime import datetime, timezone

DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "health_assistant.db"))


def _connect():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS patient_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                case_json TEXT NOT NULL,
                analysis_json TEXT NOT NULL,
                recommendation_json TEXT
            )
            """
        )


def save_case(case, analysis):
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO patient_cases (created_at, patient_name, case_json, analysis_json) VALUES (?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                case["name"],
                json.dumps(case),
                json.dumps(analysis),
            ),
        )
        return cursor.lastrowid


def list_cases():
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, created_at, patient_name, case_json, analysis_json, recommendation_json "
            "FROM patient_cases ORDER BY id DESC"
        ).fetchall()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "patient": json.loads(row["case_json"]),
            "analysis": json.loads(row["analysis_json"]),
            "recommendation": json.loads(row["recommendation_json"]) if row["recommendation_json"] else None,
        }
        for row in rows
    ]


def save_recommendation(case_id, recommendation):
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE patient_cases SET recommendation_json = ? WHERE id = ?",
            (json.dumps(recommendation), case_id),
        )
        return cursor.rowcount > 0
