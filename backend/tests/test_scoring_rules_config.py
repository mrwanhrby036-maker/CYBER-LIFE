import json
from pathlib import Path
import pytest
from app.service_scoring import score_question, score_assessment
from app.helpers import normalize_answer
from app.errors import ValidationError
from app.config import Settings

ROOT = Path(__file__).resolve().parents[2]


def test_normalize_arabic():
    assert normalize_answer("أحمد") == normalize_answer("احمد")
    assert normalize_answer("مدرسة") == normalize_answer("مدرسه")


def test_mcq_scoring():
    q = {"id": "q1", "type": "mcq", "answer": "a", "points": 2, "explanation": "x"}
    assert score_question(q, "a")["earned"] == 2
    assert score_question(q, "b")["earned"] == 0


def test_multi_partial_penalty():
    q = {"id": "q1", "type": "multi", "answer": ["a", "b"], "points": 2}
    assert score_question(q, ["a"])["earned"] == 1
    assert score_question(q, ["a", "b"])["earned"] == 2
    assert score_question(q, ["a", "c"])["earned"] == 0


def test_report_rubric_not_length():
    q = {"id": "r", "type": "report", "points": 3, "rubric": [
        {"id": "a", "label": "دليل", "weight": 1, "any_of": [["سجل", "دليل"]]},
        {"id": "b", "label": "إجراء", "weight": 2, "any_of": [["عزل", "احتواء"]]}
    ]}
    short = score_question(q, "سجل")
    full = score_question(q, "السجل يشير إلى حادث ونوصي بعزل الجهاز")
    assert full["earned"] > short["earned"]
    assert full["earned"] == 3


def test_assessment_missing_and_duplicate():
    a = {"id": "a", "questions": [{"id": "q1", "type": "mcq", "answer": "a"}]}
    class Ans:
        def __init__(self, qid, answer): self.question_id = qid; self.answer = answer
    with pytest.raises(ValidationError):
        score_assessment(a, [])
    with pytest.raises(ValidationError):
        score_assessment(a, [Ans("q1", "a"), Ans("q1", "a")])
    result = score_assessment(a, [Ans("q1", "a")])
    assert result["percentage"] == 100


def test_database_rules_deny_public_write():
    rules = json.loads((ROOT / "database" / "database.rules.json").read_text(encoding="utf-8"))["rules"]
    assert rules[".write"] is False
    assert rules[".read"] is False
    assert rules["assessment_keys"][".read"] is False
    assert rules["audit_logs"][".write"] is False
    assert "admin_roles" in rules["audit_logs"][".read"]


def test_production_rejects_local_modes():
    with pytest.raises(Exception):
        Settings(env="production", auth_mode="local", storage_mode="local",
                 cors_origins="https://app.example.com")
    with pytest.raises(Exception):
        Settings(env="production", auth_mode="firebase", storage_mode="firebase",
                 firebase_database_url="", firebase_credentials_file="")


def test_firebase_requires_https_database_url():
    with pytest.raises(Exception):
        Settings(firebase_database_url="http://hamo-8132e.firebaseio.com")
