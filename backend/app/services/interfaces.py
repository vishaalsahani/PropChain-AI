"""Engine interfaces for the PropChain analysis pipeline.

These contracts deliberately depend on nothing but the standard library and
plain strings/dicts: no ORM models, no framework imports. That keeps the
pipeline components swappable (mock -> real OCR/NLP/rule engines) without
touching ``app.models`` and lets the same code run inside scripts and tests.

Severity values follow the ORM enum values: "low", "medium", "high", "critical".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class OcrPage:
    """A single OCR'd page of a document."""

    page_number: int
    text: str
    confidence: float | None = None


@dataclass
class OcrResult:
    """Full OCR output for one document."""

    pages: list[OcrPage]
    language: str | None
    engine_version: str


@dataclass
class ClassificationResult:
    """Document type guess produced by a classifier."""

    doc_type: str
    confidence: float
    engine_version: str


@dataclass
class FieldCandidate:
    """One extracted field value with provenance for review/audit."""

    field_name: str
    raw_value: str | None
    value_type: str = "string"
    confidence: float | None = None
    page: int | None = None
    snippet: str | None = None


@dataclass
class FlagDraft:
    """A risk flag before it is persisted.

    ``severity`` uses the ORM severity values ("low", "medium", "high",
    "critical") and ``rule_ref`` is the stable rule identifier (e.g.
    "MH-CHAIN-001") so drafts can be traced back to a rule or validator.
    """

    category: str
    title: str
    description: str
    severity: str
    confidence: float
    evidence: str | None = None
    rule_ref: str | None = None
    recommended_action: str | None = None


@dataclass
class OwnershipDraft:
    """One step of the ownership chain, ordered by ``sequence``."""

    from_party: str | None
    to_party: str
    transfer_type: str
    transfer_date: str | None
    document_ref: str | None
    sequence: int
    gap_flag: bool = False


@runtime_checkable
class OcrService(Protocol):
    """Turns a stored file path into text."""

    @property
    def engine_version(self) -> str: ...

    def extract(self, path: str, languages: list[str]) -> OcrResult: ...


@runtime_checkable
class DocClassifier(Protocol):
    """Maps a filename (plus optional OCR text) to a document type."""

    @property
    def engine_version(self) -> str: ...

    def classify(self, filename: str, text: str | None = None) -> ClassificationResult: ...


@runtime_checkable
class NLPExtractor(Protocol):
    """Pulls structured fields out of OCR text for a known document type."""

    @property
    def engine_version(self) -> str: ...

    def extract(self, doc_type: str, ocr_text: str) -> list[FieldCandidate]: ...


@runtime_checkable
class CrossValidator(Protocol):
    """Compares extractions across documents of one property.

    ``extracted`` and ``document_meta`` are keyed by document id;
    ``document_meta`` entries carry at least a "filename" key.
    """

    @property
    def engine_version(self) -> str: ...

    def validate(self, extracted: dict[int, dict], document_meta: dict[int, dict]) -> list[FlagDraft]: ...


@runtime_checkable
class OwnershipGraphBuilder(Protocol):
    """Builds the ownership chain from document metadata (keyed by document id)."""

    @property
    def engine_version(self) -> str: ...

    def build(self, document_meta: dict[int, dict]) -> list[OwnershipDraft]: ...


@runtime_checkable
class RuleEngine(Protocol):
    """Evaluates Maharashtra due-diligence rules for a property profile."""

    @property
    def engine_version(self) -> str: ...

    def evaluate(self, property_profile: dict, extracted: list[dict]) -> list[FlagDraft]: ...
