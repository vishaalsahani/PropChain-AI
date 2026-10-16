"""SQLAlchemy models — Phase 1 domain model (the 19 analysis classes, Review-III slide 11).

Table names follow the specification entities. Two pre-Phase-1 tables were renamed by
migration 0002: ``findings`` -> ``risk_flags`` and ``ownership_nodes`` ->
``ownership_records``; transition aliases (``Finding``, ``OwnershipNode``) are kept at the
bottom until every call site is updated.

The decks carry no attribute lists for the entity classes, so fields beyond the
specification's stated requirements are project-defined. Fields marked "(project-defined)"
exist to satisfy the Responsible-AI constraints (evidence, source page, confidence,
explicit unknown states) and the run-history requirement (immutable AnalysisRun).
"""

from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeEngine

from app.database import Base
from app.models.enums import (
    AnalysisRunStatus,
    AreaUnit,
    BlockchainRecordStatus,
    DocumentStatus,
    FieldValueStatus,
    FindingSeverity,
    PropertyStatus,
    RiskCategory,
    Severity,
    UserRole,
    Verdict,
    db_enum,
)

# JSON on SQLite, JSONB on PostgreSQL.
JsonType: TypeEngine = JSON().with_variant(JSONB, "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(db_enum(UserRole), default=UserRole.buyer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=utcnow)

    properties: Mapped[list["Property"]] = relationship(back_populates="owner")


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(100), default="Maharashtra")
    district: Mapped[str] = mapped_column(String(100), default="")
    taluka: Mapped[str] = mapped_column(String(100), default="")
    village: Mapped[str] = mapped_column(String(100), default="")
    survey_number: Mapped[str] = mapped_column(String(100), default="")
    gat_number: Mapped[str] = mapped_column(String(100), default="")
    cts_number: Mapped[str] = mapped_column(String(100), default="")
    area_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Phase 1 profile upgrade (project-defined fields).
    ulpin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    area_unit: Mapped[AreaUnit] = mapped_column(db_enum(AreaUnit), default=AreaUnit.sqft)
    boundaries: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    jurisdiction: Mapped[str] = mapped_column(String(100), default="Maharashtra")
    status: Mapped[PropertyStatus] = mapped_column(db_enum(PropertyStatus), default=PropertyStatus.draft)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="properties")
    documents: Mapped[list["Document"]] = relationship(back_populates="property", cascade="all, delete-orphan")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="property", cascade="all, delete-orphan")
    risk_flags: Mapped[list["RiskFlag"]] = relationship(back_populates="property", cascade="all, delete-orphan")
    ownership_records: Mapped[list["OwnershipRecord"]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_hash: Mapped[str] = mapped_column(String(64))
    doc_type: Mapped[str] = mapped_column(String(100), default="unknown")
    status: Mapped[DocumentStatus] = mapped_column(db_enum(DocumentStatus), default=DocumentStatus.pending)
    # Phase 1 additions (project-defined; per-page text lands in Phase 2).
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    doc_type_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # Deprecated: kept for the current frontend endpoint until ExtractedField takes over
    # (Phase 2). Do not add new writers.
    extracted_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    blockchain_tx: Mapped[str | None] = mapped_column(String(100), nullable=True)
    blockchain_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    property: Mapped["Property"] = relationship(back_populates="documents")
    extracted_fields: Mapped[list["ExtractedField"]] = relationship(back_populates="document")
    blockchain_records: Mapped[list["BlockchainRecord"]] = relationship(back_populates="document")


class AnalysisRun(Base):
    """Immutable analysis-run history — replaces delete-on-rerun (plan defect #3)."""

    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    status: Mapped[AnalysisRunStatus] = mapped_column(
        db_enum(AnalysisRunStatus), default=AnalysisRunStatus.queued
    )
    engine_version: Mapped[str] = mapped_column(String(50), default="phase-1")
    verdict: Mapped[Verdict | None] = mapped_column(db_enum(Verdict), nullable=True)  # filled in Phase 3
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    property: Mapped["Property"] = relationship(back_populates="analysis_runs")
    risk_flags: Mapped[list["RiskFlag"]] = relationship(back_populates="analysis_run")
    ownership_records: Mapped[list["OwnershipRecord"]] = relationship(back_populates="analysis_run")


class RiskFlag(Base):
    """Was ``Finding`` (table renamed in 0002). Spec entity: RiskFlag."""

    __tablename__ = "risk_flags"
    __table_args__ = (Index("ix_risk_flags_property_run", "property_id", "analysis_run_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)
    category: Mapped[RiskCategory] = mapped_column(db_enum(RiskCategory))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[Severity] = mapped_column(db_enum(Severity))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_refs: Mapped[dict | None] = mapped_column(JsonType, nullable=True)  # project-defined: doc/page/snippet
    rule_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)  # legacy string, kept for the API
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("legal_rules.id"), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)  # project-defined
    status: Mapped[str] = mapped_column(String(50), default="open")  # reviewer workflow lands in Phase 6
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    property: Mapped["Property"] = relationship(back_populates="risk_flags")
    analysis_run: Mapped["AnalysisRun | None"] = relationship(back_populates="risk_flags")
    rule: Mapped["LegalRule | None"] = relationship()


class _OwnershipCompat:
    """API-compatibility shims (Phase 1 decision D1).

    The API keeps the pre-Phase-1 field names so the frontend needs no changes. Defined in a
    mixin because the class body of OwnershipRecord shadows the builtin ``property`` with its
    SQLAlchemy relationship attribute of the same (conventional) name.
    """

    @property
    def person_name(self) -> str:
        return self.to_party

    @property
    def transaction_type(self) -> str:
        return self.transfer_type

    @property
    def transaction_date(self) -> str:
        return self.transfer_date.isoformat() if self.transfer_date else ""


class OwnershipRecord(_OwnershipCompat, Base):
    """Was ``OwnershipNode`` (table renamed in 0002). Spec entity: OwnershipRecord."""

    __tablename__ = "ownership_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)
    from_party: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_party: Mapped[str] = mapped_column(String(255))  # was person_name
    transfer_type: Mapped[str] = mapped_column(String(100))  # was transaction_type
    transfer_date: Mapped[Date | None] = mapped_column(Date, nullable=True)  # was transaction_date (string)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    document_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gap_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    property: Mapped["Property"] = relationship(back_populates="ownership_records")
    analysis_run: Mapped["AnalysisRun | None"] = relationship(back_populates="ownership_records")


class ExtractedField(Base):
    """Spec entity: ExtractedField. Populated from Phase 2 on; table lands now."""

    __tablename__ = "extracted_fields"
    __table_args__ = (Index("ix_extracted_fields_document_field", "document_id", "field_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(64), index=True)
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(32), default="string")
    value_status: Mapped[FieldValueStatus] = mapped_column(
        db_enum(FieldValueStatus), default=FieldValueStatus.present
    )
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    bbox: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extractor_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped["Document"] = relationship(back_populates="extracted_fields")


class LegalRule(Base):
    """Versioned legal rule DB (content packs land in Phase 4)."""

    __tablename__ = "legal_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rule_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(64), default="Maharashtra")
    law_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    section: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[RiskCategory | None] = mapped_column(db_enum(RiskCategory), nullable=True)
    severity: Mapped[Severity] = mapped_column(db_enum(Severity), default=Severity.medium)
    conditions: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    evidence_required: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    versions: Mapped[list["LegalRuleVersion"]] = relationship(back_populates="rule")


class LegalRuleVersion(Base):
    __tablename__ = "legal_rule_versions"
    __table_args__ = (UniqueConstraint("rule_id", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("legal_rules.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    snapshot: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    change_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    rule: Mapped["LegalRule"] = relationship(back_populates="versions")


class VerificationReport(Base):
    """Spec entity: VerificationReport (report rework lands in Phase 8)."""

    __tablename__ = "verification_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)
    verdict: Mapped[Verdict | None] = mapped_column(db_enum(Verdict), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    content: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BlockchainRecord(Base):
    """Spec entity: BlockchainRecord — fingerprints + minimum audit metadata, off-chain contents."""

    __tablename__ = "blockchain_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)
    property_id: Mapped[int | None] = mapped_column(ForeignKey("properties.id"), nullable=True, index=True)
    network: Mapped[str] = mapped_column(String(64), default="mock")
    chain_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contract_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tx_hash: Mapped[str] = mapped_column(String(128))
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    registered_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[BlockchainRecordStatus] = mapped_column(
        db_enum(BlockchainRecordStatus), default=BlockchainRecordStatus.pending
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped["Document | None"] = relationship(back_populates="blockchain_records")


class AuditEvent(Base):
    """Immutable audit trail (project-defined; DPDP-aware posture)."""

    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


# Transition aliases — remove once every call site uses the spec names.
Finding = RiskFlag
OwnershipNode = OwnershipRecord
