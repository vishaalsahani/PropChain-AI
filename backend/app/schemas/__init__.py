from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models import DocumentStatus, FindingSeverity, RiskCategory, Severity, UserRole
from app.services.rule_pack import validate_condition


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
    # Phase 4: traceability to the versioned catalogue.
    rule_id: int | None = None
    rule_version: int | None = None
    recommended_action: str | None = None
    status: str
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None

    class Config:
        from_attributes = True


class FindingReviewRequest(BaseModel):
    """Reviewer disposition for one finding."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["open", "confirmed", "dismissed", "needs_evidence"]
    note: str | None = Field(default=None, max_length=2000)
    expected_status: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def _note_is_required_for_exceptions(self):
        if self.status in {"dismissed", "needs_evidence"} and not (self.note or "").strip():
            raise ValueError("A note is required when dismissing a finding or asking for evidence.")
        return self


class RunReviewRequest(BaseModel):
    """Final human disposition for one analysis run."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["confirmed", "overridden"]
    verdict: Literal["verified", "needs_review", "flagged"] | None = None
    note: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def _verdict_matches_decision(self):
        if self.decision == "overridden" and self.verdict is None:
            raise ValueError("An overridden decision requires the final verdict.")
        if self.decision == "confirmed" and self.verdict is not None:
            raise ValueError("A confirmed decision keeps the system verdict; omit verdict.")
        return self


class AnalysisRunOut(BaseModel):
    """Run-history row (Phase 6)."""

    id: int
    property_id: int
    status: str
    engine_version: str
    verdict: str | None = None
    risk_score: float | None = None
    summary: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    created_by: int | None = None
    review_status: str = "pending"
    review_verdict: str | None = None
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    finding_count: int = 0


class ReviewQueueItemOut(BaseModel):
    property_id: int
    title: str
    village: str
    district: str
    run_id: int
    verdict: str | None = None
    risk_score: float | None = None
    review_status: str = "pending"
    review_verdict: str | None = None
    open_findings: int = 0
    total_findings: int = 0
    finished_at: datetime | None = None


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
    # Phase 6: the human review attached to this run, if any.
    review_status: str = "pending"
    review_verdict: str | None = None
    review_note: str | None = None
    reviewed_at: datetime | None = None


class BlockchainVerifyResult(BaseModel):
    document_id: int
    file_hash: str
    status: str
    blockchain_tx: str | None
    message: str
    # Phase 5: enough provenance for the UI to distinguish a real anchor from
    # the mock and to link to a block explorer.
    mode: str | None = None
    network: str | None = None
    chain_id: int | None = None
    contract_address: str | None = None
    block_number: int | None = None
    registered_hash: str | None = None


class BlockchainStatusOut(BaseModel):
    mode: str
    connected: bool
    network: str | None = None
    chain_id: int | None = None
    contract_address: str | None = None
    account: str | None = None
    message: str


class HealthOut(BaseModel):
    status: str
    app: str
    components: dict[str, str]


# ---------------------------------------------------------------------------
# Phase 4: versioned, editable rule catalogue
# ---------------------------------------------------------------------------


class RuleCreate(BaseModel):
    """A new catalogue rule. The jurisdiction comes from the URL."""

    model_config = ConfigDict(extra="forbid")

    rule_code: str = Field(min_length=3, max_length=64, pattern=r"^[A-Z0-9][A-Z0-9_-]{2,63}$")
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    category: RiskCategory
    severity: Severity = Severity.medium
    confidence: float = Field(default=0.8, ge=0, le=1)
    conditions: dict[str, Any] | None = None
    evidence_required: Any | None = None
    recommended_action: str | None = None
    law_name: str | None = Field(default=None, max_length=255)
    section: str | None = Field(default=None, max_length=64)
    source_url: str | None = Field(default=None, max_length=500)
    effective_from: date | None = None
    effective_to: date | None = None
    is_active: bool = True
    change_note: str | None = None

    @field_validator("conditions")
    @classmethod
    def _conditions_are_valid(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        validate_condition(value)
        return value

    @model_validator(mode="after")
    def _dates_are_ordered(self):
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValueError("effective_from must not be after effective_to")
        return self


class RuleUpdate(BaseModel):
    """A partial edit. Unset fields stay unchanged; explicit null clears a field."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    category: RiskCategory | None = None
    severity: Severity | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    conditions: dict[str, Any] | None = None
    evidence_required: Any | None = None
    recommended_action: str | None = None
    law_name: str | None = Field(default=None, max_length=255)
    section: str | None = Field(default=None, max_length=64)
    source_url: str | None = Field(default=None, max_length=500)
    effective_from: date | None = None
    effective_to: date | None = None
    is_active: bool | None = None
    change_note: str | None = None
    expected_version: int | None = Field(default=None, ge=1)

    @field_validator("conditions")
    @classmethod
    def _conditions_are_valid(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        validate_condition(value)
        return value

    @model_validator(mode="after")
    def _dates_are_ordered(self):
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValueError("effective_from must not be after effective_to")
        return self


class RuleVersionOut(BaseModel):
    version: int
    snapshot: dict[str, Any] | None = None
    change_note: str | None = None
    created_by: int | None = None
    created_at: datetime


class RuleOut(BaseModel):
    id: int
    rule_code: str
    jurisdiction: str
    law_name: str | None = None
    section: str | None = None
    title: str
    description: str | None = None
    category: RiskCategory | None = None
    severity: Severity
    confidence: float
    conditions: dict[str, Any] | None = None
    evidence_required: Any | None = None
    recommended_action: str | None = None
    source_url: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    is_active: bool
    current_version: int
    is_evaluable: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RuleDetailOut(RuleOut):
    versions: list[RuleVersionOut] = []


class RulePackSummaryOut(BaseModel):
    jurisdiction: str
    code: str
    name: str
    version: int
    rule_count: int
    active_rule_count: int
    evaluable_rule_count: int
    signature: str
    updated_at: datetime | None = None


class RulePackOut(RulePackSummaryOut):
    rules: list[RuleOut] = []


class RuleRollbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    change_note: str | None = None


class RuleResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_note: str | None = None
