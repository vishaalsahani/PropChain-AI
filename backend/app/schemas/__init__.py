from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.models import DocumentStatus, FindingSeverity, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=6)
    role: UserRole = UserRole.buyer


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole

    class Config:
        from_attributes = True


class PropertyCreate(BaseModel):
    title: str
    state: str = "Maharashtra"
    district: str = ""
    taluka: str = ""
    village: str = ""
    survey_number: str = ""
    gat_number: str = ""
    cts_number: str = ""
    area_sqft: float | None = None


class PropertyOut(BaseModel):
    id: int
    title: str
    state: str
    district: str
    taluka: str
    village: str
    survey_number: str
    gat_number: str
    cts_number: str
    area_sqft: float | None
    status: str
    risk_score: float | None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    property_id: int
    filename: str
    file_hash: str
    doc_type: str
    status: DocumentStatus
    extracted_data: str | None
    blockchain_tx: str | None
    blockchain_verified: bool | None
    created_at: datetime

    class Config:
        from_attributes = True


class FindingOut(BaseModel):
    id: int
    category: str
    title: str
    description: str
    severity: FindingSeverity
    confidence: float
    evidence: str | None
    rule_ref: str | None
    status: str

    class Config:
        from_attributes = True


class OwnershipNodeOut(BaseModel):
    id: int
    person_name: str
    transaction_type: str
    transaction_date: str
    document_ref: str | None
    sequence: int
    # Phase 3 (AC-5): transferor of the step and whether the link is unevidenced.
    from_party: str | None = None
    gap_flag: bool = False

    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    property_id: int
    findings: list[FindingOut]
    ownership_chain: list[OwnershipNodeOut]
    risk_score: float
    summary: str
    # Phase 3 (FR-8/AC-6): the run's verdict and the documented reasons behind it.
    verdict: str | None = None
    verdict_reasons: dict | None = None


class VerdictOut(BaseModel):
    """Latest run's verdict for one property (used by the property page)."""

    property_id: int
    analysis_run_id: int | None = None
    verdict: str | None = None
    reasons: list[str] = []
    not_checked: list[str] = []
    risk_score: float | None = None
    engine_version: str | None = None


class BlockchainVerifyResult(BaseModel):
    document_id: int
    file_hash: str
    status: str
    blockchain_tx: str | None
    message: str


class HealthOut(BaseModel):
    status: str
    app: str
    components: dict[str, str]
