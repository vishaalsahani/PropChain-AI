"""Phase 4: declarative rule-pack evaluation (no app/DB boot required)."""

from __future__ import annotations

import pytest

from app.services.interfaces import FlagDraft
from app.services.rule_pack import (
    BUILTIN_MH_RULES,
    BUILTIN_PACK_CODE,
    BUILTIN_PACK_JURISDICTION,
    RuleDefinition,
    build_context,
    evaluate_condition,
    evaluate_pack,
    pack_signature,
    validate_condition,
)
from app.services.rule_store import DatabaseRuleEngine, LoadedRulePack


def _codes(flags: list[FlagDraft]) -> list[str]:
    return [flag.rule_ref or "" for flag in flags]


def test_builtin_pack_shape_and_metadata():
    assert BUILTIN_PACK_CODE == "mh-v1"
    assert BUILTIN_PACK_JURISDICTION == "Maharashtra"
    assert len(BUILTIN_MH_RULES) == 14
    evaluable = [rule for rule in BUILTIN_MH_RULES if rule.conditions]
    assert len(evaluable) == 12
    assert {rule.rule_code for rule in evaluable} >= {
        "MH-DOC-001",
        "MH-LAND-712",
        "MH-IDENT-001",
        "MH-IDENT-002",
        "MH-CHAIN-001",
        "MH-CHAIN-002",
        "MH-CHAIN-003",
        "MH-ENC-001",
        "MH-SUCC-001",
        "MH-LIT-001",
        "MH-AREA-001",
        "MH-INTEGRITY-001",
    }
    for rule in BUILTIN_MH_RULES:
        assert rule.title
        if rule.conditions:
            assert rule.recommended_action
            assert rule.evidence_required
            assert 0 <= rule.confidence <= 1


@pytest.mark.parametrize(
    "condition",
    [
        {"type": "no_such_condition"},
        {"type": "missing_doc_type"},
        {"type": "missing_doc_type", "doc_type": "x", "typo": True},
        {"type": "document_type_present", "doc_types": []},
        {"type": "area_deviation", "tolerance": 2},
        {"type": "all", "conditions": []},
        {"type": "not", "condition": "not-an-object"},
    ],
)
def test_condition_validation_rejects_bad_shapes(condition):
    with pytest.raises(ValueError):
        validate_condition(condition)


def test_condition_validation_accepts_nested_boolean():
    validate_condition(
        {
            "type": "all",
            "conditions": [
                {"type": "state_is", "state": "Maharashtra"},
                {"type": "not", "condition": {"type": "no_documents"}},
            ],
        }
    )


def test_no_documents_short_circuits():
    flags = evaluate_pack(BUILTIN_MH_RULES, {}, [])
    assert _codes(flags) == ["MH-DOC-001"]
    assert flags[0].severity == "medium"


def test_identifier_mismatch_emits_one_finding_per_field():
    profile = {
        "state": "Maharashtra",
        "survey_number": "124/A",
        "gat_number": "318",
        "documents": [{"filename": "sale.pdf", "doc_type": "sale_deed"}],
        "ownership": [{"transfer_type": "sale", "gap_flag": False, "sequence": 1}],
    }
    extracted = [{"survey_number": "221/2", "gat_number": "999", "area_sqft": 100}]
    flags = evaluate_pack(BUILTIN_MH_RULES, profile, extracted)
    identity = [flag for flag in flags if flag.rule_ref == "MH-IDENT-002"]
    assert len(identity) == 2
    assert {flag.title for flag in identity} == {
        "Profile survey number differs from documents",
        "Profile gat number differs from documents",
    }
    assert all("sale.pdf" in (flag.evidence or "") for flag in identity)


def test_document_type_present_collects_filenames():
    profile = {
        "state": "Maharashtra",
        "documents": [
            {"filename": "sale.pdf", "doc_type": "sale_deed"},
            {"filename": "loan.pdf", "doc_type": "mortgage_deed"},
        ],
        "ownership": [{"transfer_type": "sale"}],
    }
    flags = evaluate_pack(BUILTIN_MH_RULES, profile, [])
    mortgage = next(flag for flag in flags if flag.rule_ref == "MH-ENC-001")
    assert "loan.pdf" in (mortgage.evidence or "")


def test_pack_signature_is_stable_and_version_sensitive():
    rules = list(BUILTIN_MH_RULES)
    assert pack_signature(rules) == pack_signature(list(reversed(rules)))
    changed = [
        RuleDefinition(**{**rule.__dict__, "version": 2}) if rule.rule_code == "MH-LAND-712"
        else rule
        for rule in rules
    ]
    assert pack_signature(changed) != pack_signature(rules)


def test_empty_db_catalogue_raises_a_coverage_finding():
    pack = LoadedRulePack(
        jurisdiction="Maharashtra",
        rules=[],
        signature="",
        total_count=12,
        active_count=12,
        evaluable_count=0,
        code="mh-v1",
        name="Maharashtra due-diligence screening pack",
    )
    flags = DatabaseRuleEngine(pack).evaluate({}, [])
    assert _codes(flags) == ["PACK-EMPTY-001"]
    assert flags[0].severity == "high"
    assert "not a clean verdict" in flags[0].description


def test_context_treats_unknown_verification_as_unchecked():
    context = build_context(
        {
            "documents": [
                {"filename": "a.pdf", "doc_type": "sale_deed", "blockchain_verified": None}
            ]
        },
        [],
    )
    outcome = evaluate_condition({"type": "hash_mismatch"}, context)
    assert outcome.matches == []
