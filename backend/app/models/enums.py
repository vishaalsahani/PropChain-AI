"""Domain enums for the Phase 1 domain model.

Sources:
- Document types: PropChain-AI Specs.pdf p.1 Table 2 ("Document Classification") — the
  list there is explicitly open-ended ("...and other relevant types"), so
  ``documents.doc_type`` deliberately stays a free-text column; KNOWN_DOC_TYPES lists the
  machine values the classifier should emit.
- The twelve risk categories: Specs p.4 Table 6 ("Risk Output"), verbatim. Note the
  source writes them as lowercase/hyphenated words ('land-use', 'document-integrity',
  'missing-document', 'RERA').
- Verdict: FR-8 / AC-6 (Review-III slides 3, 10, 12) — Verified / Needs Review / Flagged.
- Severity levels are a project decision: the specification says findings carry severity
  but never defines the value set.
- Field value states come from the Responsible-AI constraints (master plan 1.5): unknown /
  not checked / not applicable / source unavailable must be representable.
"""

import enum

import sqlalchemy as sa


class UserRole(str, enum.Enum):
    buyer = "buyer"
    owner = "owner"
    reviewer = "reviewer"
    admin = "admin"


class PropertyStatus(str, enum.Enum):
    draft = "draft"
    analyzing = "analyzing"
    analyzed = "analyzed"
    needs_review = "needs_review"
    flagged = "flagged"


class AreaUnit(str, enum.Enum):
    sqft = "sqft"
    sqm = "sqm"
    acre = "acre"
    hectare = "hectare"
    guntha = "guntha"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Severity(str, enum.Enum):
    """Project-defined severity levels (the spec does not define values)."""

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# Transition alias — pre-Phase-1 code imports FindingSeverity.
FindingSeverity = Severity


class RiskCategory(str, enum.Enum):
    """The twelve risk-output categories (Specs p.4 Table 6), verbatim values."""

    ownership = "ownership"
    identity = "identity"
    area = "area"
    encumbrance = "encumbrance"
    mortgage = "mortgage"
    succession = "succession"
    litigation = "litigation"
    land_use = "land-use"
    rera = "RERA"
    planning = "planning"
    document_integrity = "document-integrity"
    missing_document = "missing-document"


class Verdict(str, enum.Enum):
    """FR-8 / AC-6 verdict. Display forms: Verified / Needs Review / Flagged."""

    verified = "verified"
    needs_review = "needs_review"
    flagged = "flagged"


class AnalysisRunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class FieldValueStatus(str, enum.Enum):
    """Explicit states so "not found" is never silently treated as "absent"."""

    present = "present"
    unknown = "unknown"
    not_checked = "not_checked"
    not_applicable = "not_applicable"
    source_unavailable = "source_unavailable"


class BlockchainRecordStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"
    mock = "mock"


# Machine values for documents.doc_type (open-ended per spec; 'unknown' is the default).
KNOWN_DOC_TYPES = {
    "sale_deed",
    "agreement_to_sale",
    "gift_deed",
    "mortgage_deed",
    "lease_deed",
    "partition_deed",
    "will",
    "7_12_extract",
    "8a_record",
    "ferfar",
    "property_card",
    "ec",
    "rera",
    "court_document",
    "other",
    "unknown",
}


def db_enum(enum_cls: type[enum.Enum], **kwargs) -> sa.Enum:
    """Column-friendly enum (decision D6).

    Stored as its lowercase machine value with a CHECK constraint, on SQLite and
    PostgreSQL alike (no native PG enum types — simpler migrations).
    """

    return sa.Enum(
        enum_cls,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
        **kwargs,
    )
