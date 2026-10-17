"""Unit tests for ``app.services.cross_validate`` (Phase 3 cross-document matrix).

The engine takes plain dicts keyed by document id and returns ``FlagDraft``s, so
these tests are pure in-memory checks — no DB, no network, no OCR. Each test
asserts on the stable parts a reviewer depends on: ``rule_ref``, ``category``,
``severity`` and the evidence text (which names the documents and the values
that disagreed).

Inputs are built with two small helpers:

* :func:`pair` — two documents of the same type, the common comparison case;
* :func:`bundle` — explicit ``(doc_id, doc_type, payload)`` triples for when the
  ids or the document types matter (e.g. a ferfar quoting a sale deed).
"""

from __future__ import annotations

from app.services.cross_validate import MatrixCrossValidator
from app.services.interfaces import CrossValidator, FlagDraft

VALIDATOR = MatrixCrossValidator()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def bundle(*specs: tuple[int, str, dict]) -> tuple[dict[int, dict], dict[int, dict]]:
    """``(doc_id, doc_type, payload)`` triples -> ``(extracted, document_meta)``."""
    extracted: dict[int, dict] = {}
    document_meta: dict[int, dict] = {}
    for doc_id, doc_type, payload in specs:
        extracted[doc_id] = payload
        document_meta[doc_id] = {
            "filename": f"{doc_type}-{doc_id}.pdf",
            "doc_type": doc_type,
        }
    return extracted, document_meta


def pair(payload_a: dict, payload_b: dict, doc_type: str = "sale_deed"):
    """Two documents of one type, with document ids 1 and 2."""
    return bundle((1, doc_type, payload_a), (2, doc_type, payload_b))


def flags_for(extracted: dict[int, dict], document_meta: dict[int, dict], rule_ref: str) -> list[FlagDraft]:
    """The flags carrying ``rule_ref`` from one validation run."""
    return [
        flag
        for flag in VALIDATOR.validate(extracted, document_meta)
        if flag.rule_ref == rule_ref
    ]


def only_flag(extracted: dict[int, dict], document_meta: dict[int, dict], rule_ref: str) -> FlagDraft:
    """The single flag for ``rule_ref`` — fails loudly when it is not exactly one."""
    flags = flags_for(extracted, document_meta, rule_ref)
    assert len(flags) == 1, f"expected exactly one {rule_ref}, got {len(flags)}: {flags}"
    return flags[0]


# --------------------------------------------------------------------------
# Engine contract
# --------------------------------------------------------------------------


def test_engine_version_is_matrix_v1():
    assert MatrixCrossValidator.engine_version == "matrix-v1"
    assert VALIDATOR.engine_version == "matrix-v1"
    assert isinstance(VALIDATOR, CrossValidator)


def test_empty_inputs_return_no_flags():
    assert VALIDATOR.validate({}, {}) == []

    # A document with an empty payload states no fields, so nothing to disagree.
    empty_meta = {1: {"filename": "empty.pdf", "doc_type": "sale_deed"}}
    assert VALIDATOR.validate({1: {}}, empty_meta) == []


def test_non_dict_payloads_are_skipped():
    extracted = {1: {"survey_number": "124/A"}, 2: "not a payload", 3: None, 4: ["42"]}
    document_meta = {
        doc_id: {"filename": f"doc-{doc_id}.pdf", "doc_type": "sale_deed"}
        for doc_id in extracted
    }

    # The junk entries contribute nothing; the one real payload has no peer.
    assert VALIDATOR.validate(extracted, document_meta) == []

    # The dict payloads around them are still compared with each other.
    extracted[5] = {"survey_number": "137"}
    document_meta[5] = {"filename": "doc-5.pdf", "doc_type": "sale_deed"}
    flag = only_flag(extracted, document_meta, "MATCH-SURVEY-001")
    assert "doc-1.pdf" in flag.evidence and "doc-5.pdf" in flag.evidence


# --------------------------------------------------------------------------
# Identifiers: survey / Gat / CTS
# --------------------------------------------------------------------------


def test_survey_number_mismatch_is_flagged():
    extracted, document_meta = pair({"survey_number": "124/A"}, {"survey_number": "137"})

    flag = only_flag(extracted, document_meta, "MATCH-SURVEY-001")

    assert flag.category == "identity"
    assert flag.severity == "high"
    assert "124/A" in flag.evidence and "137" in flag.evidence
    assert "sale_deed-1.pdf" in flag.evidence and "sale_deed-2.pdf" in flag.evidence


def test_equivalent_survey_numbers_do_not_flag():
    # Case, spacing and separators are normalized before comparison.
    for variant in ("124/A", "124 / A", " 124/a "):
        extracted, document_meta = pair({"survey_number": "124/A"}, {"survey_number": variant})
        assert VALIDATOR.validate(extracted, document_meta) == [], variant


def test_gat_number_mismatch_is_flagged():
    extracted, document_meta = pair({"gat_number": "212"}, {"gat_number": "213"})

    flag = only_flag(extracted, document_meta, "MATCH-GAT-001")

    assert flag.category == "identity"
    assert flag.severity == "high"
    assert "212" in flag.evidence and "213" in flag.evidence
    assert "sale_deed-1.pdf" in flag.evidence and "sale_deed-2.pdf" in flag.evidence


def test_cts_number_mismatch_is_flagged():
    extracted, document_meta = pair({"cts_number": "56/2B"}, {"cts_number": "56/2C"})

    flag = only_flag(extracted, document_meta, "MATCH-CTS-001")

    assert flag.category == "identity"
    assert flag.severity == "high"
    assert "56/2B" in flag.evidence and "56/2C" in flag.evidence
    assert "sale_deed-1.pdf" in flag.evidence and "sale_deed-2.pdf" in flag.evidence


# --------------------------------------------------------------------------
# Names and places: owner / village / district
# --------------------------------------------------------------------------


def test_owner_name_variants_that_fuzzy_match_do_not_flag():
    # Required pair: the honorific alone must not read as a different person.
    extracted, document_meta = pair(
        {"owner_name": "Shri Rajesh Patil"}, {"owner_name": "Rajesh Patil"}
    )
    assert VALIDATOR.validate(extracted, document_meta) == []

    # Case and punctuation vary between offices too.
    extracted, document_meta = pair(
        {"owner_name": "Smt. Meena Kulkarni"}, {"owner_name": " MEENA  KULKARNI. "}
    )
    assert VALIDATOR.validate(extracted, document_meta) == []


def test_owner_name_mismatch_is_flagged():
    extracted, document_meta = pair({"owner_name": "Baban Kale"}, {"owner_name": "Rajesh Patil"})

    flag = only_flag(extracted, document_meta, "MATCH-OWNER-001")

    assert flag.category == "identity"
    assert flag.severity == "high"
    assert "Baban Kale" in flag.evidence and "Rajesh Patil" in flag.evidence
    assert "sale_deed-1.pdf" in flag.evidence and "sale_deed-2.pdf" in flag.evidence


def test_village_mismatch_is_flagged():
    extracted, document_meta = pair({"village": "Wagholi"}, {"village": "Kharadi"})

    flag = only_flag(extracted, document_meta, "MATCH-VILLAGE-001")

    assert flag.category == "identity"
    assert flag.severity == "medium"
    assert "Wagholi" in flag.evidence and "Kharadi" in flag.evidence
    assert "sale_deed-1.pdf" in flag.evidence and "sale_deed-2.pdf" in flag.evidence


def test_district_mismatch_is_flagged():
    extracted, document_meta = pair({"district": "Pune"}, {"district": "Solapur"})

    flag = only_flag(extracted, document_meta, "MATCH-DISTRICT-001")

    assert flag.category == "identity"
    assert flag.severity == "medium"
    assert "Pune" in flag.evidence and "Solapur" in flag.evidence
    assert "sale_deed-1.pdf" in flag.evidence and "sale_deed-2.pdf" in flag.evidence


# --------------------------------------------------------------------------
# Areas
# --------------------------------------------------------------------------


def test_area_within_tolerance_does_not_flag():
    # 50 sqft spread on 1300 sqft is ~3.8% — rounding, not a discrepancy.
    extracted, document_meta = pair(
        {"area_sqft": 1250.0, "area_unit": "sqft"},
        {"area_sqft": 1300.0, "area_unit": "sqft"},
    )
    assert VALIDATOR.validate(extracted, document_meta) == []


def test_area_mismatch_is_flagged():
    extracted, document_meta = pair(
        {"area_sqft": 1000.0, "area_unit": "sqft"},
        {"area_sqft": 1200.0, "area_unit": "sqft"},
    )

    flag = only_flag(extracted, document_meta, "MATCH-AREA-001")

    assert flag.category == "area"
    assert flag.severity == "medium"
    assert "1000" in flag.evidence and "1200" in flag.evidence
    assert "sale_deed-1.pdf" in flag.evidence and "sale_deed-2.pdf" in flag.evidence


# --------------------------------------------------------------------------
# Boundaries
# --------------------------------------------------------------------------


def test_boundary_descriptions_that_differ_are_flagged():
    extracted, document_meta = pair(
        {"boundaries": "North: Suresh Deshmukh plot; South: village road"},
        {"boundaries": "South: temple land; North: government land"},
    )

    flag = only_flag(extracted, document_meta, "MATCH-BOUNDARY-001")

    assert flag.category == "area"
    assert flag.severity == "medium"
    assert "village road" in flag.evidence and "temple land" in flag.evidence
    assert "sale_deed-1.pdf" in flag.evidence and "sale_deed-2.pdf" in flag.evidence


def test_near_identical_boundaries_do_not_flag():
    # Punctuation and word order vary between offices; the wording still agrees.
    extracted, document_meta = pair(
        {"boundaries": "North: Suresh Deshmukh; South: village road"},
        {"boundaries": "North - Suresh Deshmukh, South village road."},
    )
    assert VALIDATOR.validate(extracted, document_meta) == []


# --------------------------------------------------------------------------
# Registration numbers
# --------------------------------------------------------------------------


def test_reused_registration_number_is_flagged():
    # Compared after normalization (case/separators per normalize_registration_number):
    # registration numbers are unique per registered instrument.
    extracted, document_meta = pair(
        {"registration_number": "MH-PUN-2019-12345"},
        {"registration_number": "mh-pun-2019-12345"},
    )

    flag = only_flag(extracted, document_meta, "MATCH-REGNO-001")

    assert flag.category == "identity"
    assert flag.severity == "medium"
    assert "MH-PUN-2019-12345" in flag.evidence
    assert "sale_deed-1.pdf" in flag.evidence and "sale_deed-2.pdf" in flag.evidence


def test_ferfar_quoting_a_registration_number_does_not_flag():
    # A mutation (ferfar) records an instrument and quotes that instrument's
    # registration number — deliberate, so the ferfar is excluded from the check.
    extracted, document_meta = bundle(
        (1, "sale_deed", {"registration_number": "MH-PUN-2019-12345"}),
        (2, "ferfar", {"registration_number": "MH-PUN-2019-12345"}),
    )
    assert VALIDATOR.validate(extracted, document_meta) == []


# --------------------------------------------------------------------------
# Dates
# --------------------------------------------------------------------------


def test_execution_after_registration_is_flagged():
    # dd/mm/yyyy as printed; the engine compares parsed dates, not strings.
    extracted = {1: {"execution_date": "01/05/2019", "registration_date": "01/04/2019"}}
    document_meta = {1: {"filename": "late-deed.pdf", "doc_type": "sale_deed"}}

    flag = only_flag(extracted, document_meta, "MATCH-DATE-001")

    assert flag.category == "identity"
    assert flag.severity == "medium"
    assert "2019-05-01" in flag.evidence and "2019-04-01" in flag.evidence
    assert "late-deed.pdf" in flag.evidence


def test_execution_on_or_before_registration_does_not_flag():
    for execution in ("15/03/2019", "02/04/2019"):  # before, and the same day
        extracted = {1: {"execution_date": execution, "registration_date": "02/04/2019"}}
        document_meta = {1: {"filename": "deed.pdf", "doc_type": "sale_deed"}}
        assert VALIDATOR.validate(extracted, document_meta) == [], execution


# --------------------------------------------------------------------------
# Document integrity (hash verification)
# --------------------------------------------------------------------------


def test_failed_hash_verification_is_flagged():
    # The verification result the engine reads lives in the extracted payload.
    extracted = {1: {"blockchain_verified": False}}
    document_meta = {1: {"filename": "tampered.pdf", "doc_type": "sale_deed"}}

    flag = only_flag(extracted, document_meta, "MATCH-INTEGRITY-001")

    assert flag.category == "document-integrity"
    assert flag.severity == "critical"
    assert "tampered.pdf" in flag.evidence


def test_failed_hash_verification_from_document_meta_is_flagged():
    # The real pipeline passes the flag in document_meta (analysis_engine),
    # so document_meta wins when the payload does not carry the key at all.
    extracted = {1: {"survey_number": "124/A"}}
    document_meta = {
        1: {"filename": "tampered.pdf", "doc_type": "sale_deed", "blockchain_verified": False}
    }

    flag = only_flag(extracted, document_meta, "MATCH-INTEGRITY-001")

    assert flag.category == "document-integrity"
    assert flag.severity == "critical"
    assert "tampered.pdf" in flag.evidence


def test_unknown_or_successful_hash_verification_does_not_flag():
    # None means "not verified yet": unknown must never be reported as a failure.
    for verified in (None, True):
        extracted = {1: {"blockchain_verified": verified}}
        document_meta = {1: {"filename": "deed.pdf", "doc_type": "sale_deed"}}
        assert VALIDATOR.validate(extracted, document_meta) == [], verified


# --------------------------------------------------------------------------
# Nothing to compare / nothing missing
# --------------------------------------------------------------------------


def test_single_document_and_missing_fields_produce_no_flags():
    # One document alone has nothing to disagree with (and its own dates agree).
    lone = {
        "survey_number": "124/A",
        "owner_name": "Rajesh Patil",
        "village": "Wagholi",
        "area_sqft": 1000.0,
        "boundaries": "North: Suresh Deshmukh; South: village road",
        "registration_number": "MH-PUN-2019-12345",
        "execution_date": "2019-03-01",
        "registration_date": "2019-03-15",
        "blockchain_verified": True,
    }
    assert VALIDATOR.validate({1: lone}, {1: {"filename": "only.pdf", "doc_type": "sale_deed"}}) == []

    # "Unknown" is not "different": the second document simply does not state
    # the fields the first one does, so nothing is compared and nothing flags.
    extracted, document_meta = pair(
        {"area_sqft": 1000.0, "area_unit": "sqft", "owner_name": "Rajesh Patil"},
        {"registration_number": "MH-PUN-2019-1"},
    )
    assert VALIDATOR.validate(extracted, document_meta) == []
