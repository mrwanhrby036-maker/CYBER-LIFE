"""Strict input contracts. Client-supplied roles, scores and UIDs are rejected."""
from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.helpers import normalize_answer


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TeamCreate(StrictModel):
    name: str = Field(min_length=3, max_length=60)

    @field_validator("name")
    @classmethod
    def team_name(cls, value: str) -> str:
        if not any(c.isalnum() for c in value) or any(c in value for c in "<>/$#[]\x00"):
            raise ValueError("اسم الفريق يجب أن يحتوي حروفاً أو أرقاماً دون رموز برمجية")
        return value


class ProfileUpdate(StrictModel):
    display_name: str = Field(min_length=2, max_length=80)
    school: str = Field(default="", max_length=120)
    governorate: str = Field(default="", max_length=80)


class AnswerSubmission(StrictModel):
    question_id: str = Field(min_length=1, max_length=128)
    answer: str | list[str] = Field(max_length=16000)


class AssessmentSubmission(StrictModel):
    answers: list[AnswerSubmission] = Field(min_length=1, max_length=40)


class LessonCompletion(StrictModel):
    exercise_answer: str | list[str] = Field(max_length=16000)
    assessment: AssessmentSubmission


class LabCommand(StrictModel):
    command: str = Field(min_length=1, max_length=1000)


class LabValidation(StrictModel):
    exercise_id: str = Field(min_length=1, max_length=128)
    answers: list[AnswerSubmission] = Field(default_factory=list, max_length=20)


class ReportSubmission(StrictModel):
    title: str = Field(min_length=5, max_length=160)
    summary: str = Field(min_length=30, max_length=4000)
    evidence: str = Field(min_length=30, max_length=6000)
    analysis: str = Field(min_length=50, max_length=6000)
    actions: str = Field(min_length=30, max_length=4000)
    mission_id: str = Field(default="", max_length=128)


class MissionDecision(StrictModel):
    question_id: str = Field(min_length=1, max_length=128)
    choice_id: str = Field(min_length=1, max_length=128)
    justification: str = Field(min_length=15, max_length=3000)


class MissionFindings(StrictModel):
    findings: str = Field(min_length=30, max_length=6000)
    actions: str = Field(min_length=30, max_length=4000)


class MissionTransition(StrictModel):
    state: Literal["assigned", "investigating", "evidence_collected", "under_review", "resolved", "closed"]


class RoleUpdate(StrictModel):
    role: Literal["student", "admin"]


class ContentPublish(StrictModel):
    published: bool


class LocalLogin(StrictModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)


class AdminContent(StrictModel):
    """Allowlisted editable fields; nested content is validated by ContentService."""
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=3000)
    data: dict[str, Any] = Field(default_factory=dict)
    published: bool = False
