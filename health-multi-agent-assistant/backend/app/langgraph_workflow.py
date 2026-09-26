# Optional reference implementation showing how the same workflow
# can be modeled with LangGraph. The API currently uses the lightweight
# agents.py implementation so the project runs even without a model API key.

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class HealthState(TypedDict, total=False):
    case: dict
    language: str
    summary: dict
    triage: str
    doctor_review_required: bool

def language_node(state):
    state["language"] = state["case"].get("language", "en")
    return state

def intake_node(state):
    c = state["case"]
    state["summary"] = {
        "name": c["name"], "age": c["age"],
        "symptoms": c["symptoms"], "duration": c.get("duration",""),
        "allergies": c.get("allergies",""),
        "current_medicines": c.get("current_medicines",""),
        "medical_history": c.get("medical_history","")
    }
    return state

def triage_node(state):
    state["triage"] = "doctor_review"
    state["doctor_review_required"] = True
    return state

def build_graph():
    g = StateGraph(HealthState)
    g.add_node("language", language_node)
    g.add_node("intake", intake_node)
    g.add_node("triage", triage_node)
    g.add_edge(START, "language")
    g.add_edge("language", "intake")
    g.add_edge("intake", "triage")
    g.add_edge("triage", END)
    return g.compile()
