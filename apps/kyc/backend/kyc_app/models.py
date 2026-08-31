"""KYC case domain model and lifecycle states."""

from enum import Enum

from pydantic import BaseModel


class KycState(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class KycCase(BaseModel):
    id: str
    applicant_name: str
    email: str
    country: str
    risk_score: int  # 0-100
    documents: list[str]
    state: KycState
    submitted_at: str
    reviewer_id: str | None = None
    resolution_note: str | None = None


class StartReviewInput(BaseModel):
    pass


class EscalateInput(BaseModel):
    reason: str


class ApproveInput(BaseModel):
    note: str = ""


class RejectInput(BaseModel):
    reason: str
