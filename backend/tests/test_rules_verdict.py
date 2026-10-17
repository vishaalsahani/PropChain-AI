"""Tests for the Phase 3 rule pack (``rules_mh``) and the verdict policy.

Standalone by design, mirroring ``test_classifier_keyword.py``: no conftest
fixtures, no app boot, no DB, no network — only the two engine modules plus the
dataclasses they exchange (``FlagDraft`` / ``OwnershipDraft``).

Two layers are covered:

* ``app.services.rules_mh.MaharashtraRuleEngine`` — every rule id in the v1 pack
  fires on its documented trigger (right category and severity) and stays quiet
  otherwise;
* ``app.services.verdict.derive_verdict`` — the documented policy mapping
  (Verified / Needs Review / Flagged), the reason list, and the explicit
  "not checked" list the Responsible-AI rule demands.

The profile/extraction shapes are the ones the pipeline passes in: the enriched
``property_profile`` (documents + ownership chain) and one dict per document
extraction.
"""

from __future__ import annotations

import pytest

from app.services.interfaces import FlagDraft, OwnershipDraft
from app.services.rules_mh import MaharashtraRuleEngine
from app.services.verdict import MAX_REASONS, derive_verdict

#: Version reported by the rule pack (also a contract in the protocol).
ENGINE_VERSION = "mh-v1"

#: Severities the ORM vocabulary allows.
SEVERITIES = {"low", "medium", "high", "critical"}


# --------------------------------------------------------------------------
# Builders / small helpers
# --------------------------------------------------------------------------


def _doc(
    doc_type: str = "sale_deed",
    filename: str = "x.pdf",
    doc_id: int = 1,
    blockchain_verified: bool | None = None,
) -> dict:
    """One entry of ``profile["documents"]`` as the pipeline stores it."""
    return {
        "doc_id": doc_id,
        "filename": filename,
        "doc_type": doc_type,
        "blockchain_verified": blockchain_verified,
    }


def _node(
    from_party: str | None = "A",
    to_party: str = "B",
    transfer_type: str = "sale",
    sequence: int = 1,
    gap_flag: bool = False,
    document_ref: str | None = "x.pdf",
) -> dict:
    """One ownership step of ``profile["ownership"]``."""
    return {
        "from_party": from_party,
        "to_party": to_party,
        "transfer_type": transfer_type,
        "transfer_date": "2019-03-15",
        "document_ref": document_ref,
        "sequence": sequence,
        "gap_flag": gap_flag,
    }


def _profile(**overrides) -> dict:
    """The canonical Maharashtra profile from the brief; overrides win."""
    profile = {
        "state": "Maharashtra",
        "survey_number": "124/A",
        "area_sqft": 1200.0,
        "documents": [_doc()],
        "ownership": [_node()],
    }
    profile.update(overrides)
    return profile


def _engine() -> MaharashtraRuleEngine:
    return MaharashtraRuleEngine()


def _refs(flags: list[FlagDraft]) -> list[str | None]:
    return [flag.rule_ref for flag in flags]


def _by_ref(flags: list[FlagDraft], rule_ref: str) -> list[FlagDraft]:
    return [flag for flag in flags if flag.rule_ref == rule_ref]


def _one(flags: list[FlagDraft], rule_ref: str) -> FlagDraft:
    """The single finding for ``rule_ref``; a clear failure when it is absent."""
    matches = _by_ref(flags, rule_ref)
    assert len(matches) == 1, f"expected exactly one {rule_ref}, got {_refs(flags)}"
    return matches[0]


def _flag(
    severity: str = "high",
    title: str = "Ownership chain has an unevidenced step",
    rule_ref: str = "MH-CHAIN-001",
) -> FlagDraft:
    """A minimal draft standing in for a rule finding."""
    return FlagDraft(
        category="ownership",
        title=title,
        description="A screening indicator raised by the automated rules.",
        severity=severity,
        confidence=0.8,
        evidence="Step 1: A -> B (x.pdf)",
        rule_ref=rule_ref,
    )


def _step(
    gap_flag: bool = False,
    from_party: str | None = "A",
    to_party: str = "B",
    sequence: int = 1,
    document_ref: str | None = "x.pdf",
) -> OwnershipDraft:
    """An ownership step as the graph builder hands it to the verdict policy."""
    return OwnershipDraft(
        from_party=from_party,
        to_party=to_party,
        transfer_type="sale",
        transfer_date="2019-03-15",
        document_ref=document_ref,
        sequence=sequence,
        gap_flag=gap_flag,
    )


def _verdict_documents(*doc_types: str) -> list[dict]:
    """Minimal document list for the verdict policy (only ``doc_type`` matters)."""
    return [{"doc_type": doc_type} for doc_type in doc_types]


# --------------------------------------------------------------------------
# MH-DOC-001 / MH-LAND-712 — missing documents
# --------------------------------------------------------------------------


def test_no_documents_yields_only_mh_doc_001():
    flags = _engine().evaluate({}, [])
    assert _refs(flags) == ["MH-DOC-001"]
    assert flags[0].category == "missing-document"
    assert flags[0].severity == "medium"


def test_missing_7_12_among_documents_is_high():
    flag = _one(_engine().evaluate(_profile(), []), "MH-LAND-712")
    assert flag.category == "missing-document"
    assert flag.severity == "high"


def test_7_12_document_suppresses_mh_land_712():
    profile = _profile(
        documents=[
            _doc(doc_id=1),
            _doc(doc_type="7_12_extract", filename="712.pdf", doc_id=2),
        ]
    )
    assert "MH-LAND-712" not in _refs(_engine().evaluate(profile, []))


def test_extraction_only_profile_still_evaluates_land_record():
    """No ``documents`` key: doc types come from the extraction list instead."""
    profile = {"state": "Maharashtra", "survey_number": "124/A", "area_sqft": 1200.0}
    extracted = [
        {"doc_type": "7_12_extract", "survey_number": "124/A", "area_sqft": 1200.0}
    ]
    flags = _engine().evaluate(profile, extracted)
    assert "MH-LAND-712" not in _refs(flags)
    assert "MH-DOC-001" not in _refs(flags)


# --------------------------------------------------------------------------
# MH-IDENT-001 / MH-IDENT-002 — identity
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "state,survey_number,expected",
    [
        ("Maharashtra", None, True),
        ("Maharashtra", "124/A", False),
        ("Gujarat", None, False),
    ],
    ids=["mh-without-identifier", "mh-with-identifier", "other-state-without-identifier"],
)
def test_mh_ident_001_needs_maharashtra_and_a_missing_identifier(
    state, survey_number, expected
):
    profile = _profile(state=state, survey_number=survey_number)
    flags = _engine().evaluate(profile, [])
    assert ("MH-IDENT-001" in _refs(flags)) is expected
    if expected:
        assert _one(flags, "MH-IDENT-001").category == "identity"


def test_mh_ident_002_reports_both_identifiers():
    extracted = [
        {"doc_type": "sale_deed", "survey_number": "221/2", "area_sqft": 1200.0}
    ]
    flag = _one(_engine().evaluate(_profile(), extracted), "MH-IDENT-002")
    assert flag.category == "identity"
    assert flag.severity == "high"
    assert "124/A" in flag.evidence
    assert "221/2" in flag.evidence


def test_mh_ident_002_ignores_equivalent_spellings():
    """Same identifier, different spacing/case: normalization makes them agree."""
    extracted = [
        {"doc_type": "sale_deed", "survey_number": " 124 / a ", "area_sqft": 1200.0}
    ]
    assert "MH-IDENT-002" not in _refs(_engine().evaluate(_profile(), extracted))


# --------------------------------------------------------------------------
# MH-CHAIN-001..003 — ownership chain
# --------------------------------------------------------------------------


def test_ownership_gap_is_high_and_names_the_step():
    flag = _one(
        _engine().evaluate(_profile(ownership=[_node(gap_flag=True)]), []),
        "MH-CHAIN-001",
    )
    assert flag.category == "ownership"
    assert flag.severity == "high"
    assert "Step 1" in flag.evidence
    assert "x.pdf" in flag.evidence


def test_continuous_ownership_raises_no_gap_finding():
    ownership = [
        _node(),
        _node(sequence=2, from_party="B", to_party="C", document_ref="y.pdf"),
    ]
    assert "MH-CHAIN-001" not in _refs(_engine().evaluate(_profile(ownership=ownership), []))


def test_agreement_only_ownership_is_mh_chain_002():
    flag = _one(
        _engine().evaluate(_profile(ownership=[_node(transfer_type="agreement")]), []),
        "MH-CHAIN-002",
    )
    assert flag.category == "ownership"
    assert flag.severity == "medium"


def test_agreement_followed_by_a_registered_sale_is_not_mh_chain_002():
    ownership = [
        _node(transfer_type="agreement", sequence=1),
        _node(sequence=2, from_party="B", to_party="C", transfer_type="sale"),
    ]
    flags = _engine().evaluate(_profile(ownership=ownership), [])
    assert "MH-CHAIN-002" not in _refs(flags)


def test_empty_ownership_chain_is_mh_chain_003():
    flags = _engine().evaluate(_profile(ownership=[]), [])
    flag = _one(flags, "MH-CHAIN-003")
    assert flag.category == "ownership"
    assert flag.severity == "medium"
    assert "MH-CHAIN-001" not in _refs(flags)
    assert "MH-CHAIN-002" not in _refs(flags)

    profile_without_key = _profile()
    profile_without_key.pop("ownership")
    assert "MH-CHAIN-003" in _refs(_engine().evaluate(profile_without_key, []))


# --------------------------------------------------------------------------
# MH-ENC-001 / MH-SUCC-001 / MH-LIT-001 — charges, succession, litigation
# --------------------------------------------------------------------------


def test_mortgage_deed_is_reported_with_the_filename():
    documents = [
        _doc(doc_id=1),
        _doc(doc_type="mortgage_deed", filename="loan_2018.pdf", doc_id=2),
    ]
    flag = _one(_engine().evaluate(_profile(documents=documents), []), "MH-ENC-001")
    assert flag.category == "mortgage"
    assert "loan_2018.pdf" in flag.evidence


@pytest.mark.parametrize(
    "doc_type,expected",
    [("will", True), ("partition_deed", True), ("sale_deed", False)],
)
def test_succession_documents_trigger_mh_succ_001(doc_type, expected):
    documents = [
        _doc(doc_id=1),
        _doc(doc_type=doc_type, filename=f"{doc_type}.pdf", doc_id=2),
    ]
    flags = _engine().evaluate(_profile(documents=documents), [])
    assert ("MH-SUCC-001" in _refs(flags)) is expected
    if expected:
        flag = _one(flags, "MH-SUCC-001")
        assert flag.category == "succession"
        assert f"{doc_type}.pdf" in flag.evidence


def test_court_document_triggers_mh_lit_001():
    documents = [
        _doc(doc_id=1),
        _doc(doc_type="court_document", filename="suit_245_2019.pdf", doc_id=2),
    ]
    flag = _one(_engine().evaluate(_profile(documents=documents), []), "MH-LIT-001")
    assert flag.category == "litigation"
    assert "suit_245_2019.pdf" in flag.evidence


# --------------------------------------------------------------------------
# MH-AREA-001 / MH-INTEGRITY-001
# --------------------------------------------------------------------------


def test_area_outside_tolerance_is_mh_area_001():
    extracted = [
        {"doc_type": "sale_deed", "survey_number": "124/A", "area_sqft": 1300.0}
    ]
    flag = _one(_engine().evaluate(_profile(area_sqft=1000.0), extracted), "MH-AREA-001")
    assert flag.category == "area"
    assert "1000" in flag.evidence
    assert "1300" in flag.evidence


def test_area_within_five_percent_is_not_flagged():
    extracted = [
        {"doc_type": "sale_deed", "survey_number": "124/A", "area_sqft": 1030.0}
    ]
    flags = _engine().evaluate(_profile(area_sqft=1000.0), extracted)
    assert "MH-AREA-001" not in _refs(flags)


def test_blockchain_mismatch_is_critical():
    profile = _profile(
        documents=[_doc(filename="changed.pdf", blockchain_verified=False)]
    )
    flag = _one(_engine().evaluate(profile, []), "MH-INTEGRITY-001")
    assert flag.category == "document-integrity"
    assert flag.severity == "critical"
    assert "changed.pdf" in flag.evidence


@pytest.mark.parametrize("verified", [None, True], ids=["unrecorded", "verified"])
def test_verified_or_unrecorded_hash_is_not_flagged(verified):
    profile = _profile(documents=[_doc(blockchain_verified=verified)])
    assert "MH-INTEGRITY-001" not in _refs(_engine().evaluate(profile, []))


# --------------------------------------------------------------------------
# Engine contract
# --------------------------------------------------------------------------


def test_engine_version_and_minimal_profile():
    engine = _engine()
    assert MaharashtraRuleEngine.engine_version == ENGINE_VERSION == "mh-v1"
    flags = engine.evaluate({"state": "Maharashtra"}, [])
    assert _refs(flags) == ["MH-DOC-001"]


def test_every_emitted_finding_is_traceable_and_well_formed():
    """A profile that trips most rules: every draft must be usable as a finding."""
    profile = _profile(
        documents=[
            _doc(doc_type="sale_deed", filename="sale_2019.pdf", doc_id=1),
            _doc(doc_type="mortgage_deed", filename="loan_2018.pdf", doc_id=2),
            _doc(
                doc_type="will",
                filename="will_2020.pdf",
                doc_id=3,
                blockchain_verified=False,
            ),
            _doc(doc_type="court_document", filename="suit_245_2019.pdf", doc_id=4),
        ],
        ownership=[
            _node(gap_flag=True),
            _node(
                sequence=2,
                from_party="B",
                to_party="C",
                transfer_type="agreement",
                document_ref="agreement.pdf",
            ),
        ],
    )
    extracted = [
        {"doc_type": "sale_deed", "survey_number": "221/2", "area_sqft": 5000.0}
    ]
    flags = _engine().evaluate(profile, extracted)

    expected = {
        "MH-LAND-712",
        "MH-IDENT-002",
        "MH-CHAIN-001",
        "MH-ENC-001",
        "MH-SUCC-001",
        "MH-LIT-001",
        "MH-AREA-001",
        "MH-INTEGRITY-001",
    }
    assert expected <= set(_refs(flags))
    assert "MH-CHAIN-002" not in _refs(flags)  # a registered sale step is present

    for flag in flags:
        assert flag.rule_ref and flag.title and flag.description
        assert flag.evidence
        assert flag.recommended_action
        assert flag.severity in SEVERITIES
        assert 0.0 <= flag.confidence <= 1.0


# --------------------------------------------------------------------------
# Verdict policy — verdict mapping
# --------------------------------------------------------------------------


def test_no_documents_needs_review():
    outcome = derive_verdict([], [], [])
    assert outcome.verdict == "needs_review"
    assert any("No documents" in reason for reason in outcome.reasons)


def test_high_severity_finding_flags_with_its_title_and_rule_ref():
    draft = _flag(severity="high", title="Court document among the documents")
    outcome = derive_verdict([draft], [], _verdict_documents("sale_deed"))
    assert outcome.verdict == "flagged"
    joined = " ".join(outcome.reasons)
    assert draft.title in joined
    assert draft.rule_ref in joined


def test_critical_finding_flags_and_outranks_high():
    critical = _flag(
        severity="critical",
        title="Registered hash does not match the file",
        rule_ref="MH-INTEGRITY-001",
    )
    high = _flag(
        severity="high",
        title="Court document among the documents",
        rule_ref="MH-LIT-001",
    )
    outcome = derive_verdict([high, critical], [], _verdict_documents("sale_deed"))
    assert outcome.verdict == "flagged"
    assert outcome.reasons[0].startswith("Critical:")
    assert outcome.reasons[1].startswith("High:")


@pytest.mark.parametrize(
    "severity,expected",
    [
        ("critical", "flagged"),
        ("high", "flagged"),
        ("medium", "needs_review"),
        ("low", "needs_review"),
    ],
)
def test_severity_decides_the_verdict(severity, expected):
    outcome = derive_verdict(
        [_flag(severity=severity)], [], _verdict_documents("sale_deed")
    )
    assert outcome.verdict == expected


def test_no_findings_verifies_the_run():
    outcome = derive_verdict([], [], _verdict_documents("sale_deed"))
    assert outcome.verdict == "verified"
    assert outcome.reasons  # even Verified explains itself to the reviewer


def test_ownership_gap_alone_flags_and_names_the_parties():
    step = _step(
        gap_flag=True,
        from_party="Suresh Deshmukh",
        to_party="Rajesh Patil",
        sequence=2,
        document_ref="sale_deed_2019.pdf",
    )
    outcome = derive_verdict([], [step], _verdict_documents("sale_deed"))
    assert outcome.verdict == "flagged"
    joined = " ".join(outcome.reasons)
    assert "Suresh Deshmukh" in joined
    assert "Rajesh Patil" in joined
    assert "2" in joined


# --------------------------------------------------------------------------
# Verdict policy — not_checked and serialization
# --------------------------------------------------------------------------


def test_not_checked_lists_the_checks_that_could_not_run():
    outcome = derive_verdict([], [], _verdict_documents("sale_deed"))
    joined = " ".join(outcome.not_checked)
    assert "RERA" in joined
    assert "Court/litigation" in joined
    assert "Encumbrance" in joined  # no ec / mortgage_deed among the documents
    assert all("not checked" in entry for entry in outcome.not_checked)


def test_not_checked_entries_disappear_when_the_documents_exist():
    documents = _verdict_documents("sale_deed", "rera", "court_document", "ec")
    outcome = derive_verdict([], [], documents)
    joined = " ".join(outcome.not_checked)
    assert "RERA" not in joined
    assert "Court/litigation" not in joined
    assert "Encumbrance" not in joined
    # Still unchecked: no land record or sanctioned plan was uploaded.
    assert "Planning/land-use" in joined


def test_to_dict_has_exactly_the_three_documented_keys():
    outcome = derive_verdict([], [], _verdict_documents("sale_deed"))
    payload = outcome.to_dict()
    assert set(payload) == {"verdict", "reasons", "not_checked"}
    assert payload["verdict"] == outcome.verdict
    assert payload["reasons"] == list(outcome.reasons)
    assert payload["not_checked"] == list(outcome.not_checked)

    payload["reasons"].append("mutation must not leak back")
    assert outcome.reasons != payload["reasons"]  # to_dict hands out copies


def test_reasons_are_capped_at_max_reasons():
    drafts = [
        _flag(severity="high", title=f"Finding {index}", rule_ref=f"MH-TEST-{index:03d}")
        for index in range(1, 9)
    ]
    outcome = derive_verdict(drafts, [], _verdict_documents("sale_deed"))
    assert outcome.verdict == "flagged"
    assert len(outcome.reasons) == MAX_REASONS == 6
