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

    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    property_id: int
    findings: list[FindingOut]
    ownership_chain: list[OwnershipNodeOut]
    risk_score: float
    summary: str


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
