"""Generator tests for the AC-3 seeded-error corpus (scripts/make_error_set.py).

The AC-3 report itself needs Tesseract, so it runs out-of-band (like the AC-2
harness); these tests pin what can be checked without OCR: the corpus is
generated deterministically, every case carries the documents its manifest
promises, and the expected rule refs stay inside the frozen engine vocabulary.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import make_error_set  # noqa: E402  (needs the scripts directory on sys.path)

import pymupdf  # noqa: E402


def _pdf_text(path: Path) -> list[str]:
    with pymupdf.open(path) as doc:
        return [page.get_text() for page in doc]

#: The rule refs matrix-v1 / mh-v1 can emit. Authoritative source: the two
#: engine modules; this set is the corpus's contract with them, so a rename
#: fails this test loudly instead of silently missing in the AC-3 report.
KNOWN_RULE_REFS = {
    "MATCH-SURVEY-001", "MATCH-GAT-001", "MATCH-CTS-001", "MATCH-OWNER-001",
    "MATCH-VILLAGE-001", "MATCH-DISTRICT-001", "MATCH-AREA-001", "MATCH-BOUNDARY-001",
    "MATCH-REGNO-001", "MATCH-DATE-001", "MATCH-INTEGRITY-001",
    "MH-DOC-001", "MH-LAND-712", "MH-IDENT-001", "MH-IDENT-002", "MH-CHAIN-001",
    "MH-CHAIN-002", "MH-CHAIN-003", "MH-ENC-001", "MH-SUCC-001", "MH-LIT-001",
    "MH-AREA-001", "MH-INTEGRITY-001",
}

CONTROL_CASES = {"control_clean", "control_clean__mr"}
EXPECTED_CASE_COUNT = 21


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> tuple[Path, list[dict]]:
    out_dir = tmp_path_factory.mktemp("error_set")
    assert make_error_set.main(["--out", str(out_dir)]) == 0
    manifest = json.loads((out_dir / "_cases.json").read_text(encoding="utf-8"))
    return out_dir, manifest


def test_generator_writes_every_case_with_its_documents(corpus):
    out_dir, manifest = corpus

    assert len(manifest) == EXPECTED_CASE_COUNT
    for entry in manifest:
        case_dir = out_dir / entry["name"]
        assert case_dir.is_dir(), entry["name"]
        for document in entry["documents"]:
            path = case_dir / document["filename"]
            assert path.is_file() and path.stat().st_size > 0, path
            assert document["doc_type"] in {
                "sale_deed", "ferfar", "7_12_extract", "ec", "property_card",
                "agreement_to_sale", "mortgage_deed", "will", "court_document",
            }


def test_manifest_expectations_stay_in_the_engine_vocabulary(corpus):
    _, manifest = corpus

    for entry in manifest:
        expected = entry["expect"]["rule_refs"]
        if entry["name"] in CONTROL_CASES:
            assert expected == [], entry["name"]
            assert entry["expect"]["verdict"] == "verified", entry["name"]
        else:
            assert expected, f"{entry['name']} seeds an error but expects no finding"
            for ref in expected:
                assert ref in KNOWN_RULE_REFS, f"{entry['name']}: unknown rule ref {ref}"


def test_corpus_covers_both_languages_and_several_error_families(corpus):
    _, manifest = corpus

    languages = {entry["language"] for entry in manifest}
    assert languages == {"english", "marathi"}

    refs = {ref for entry in manifest for ref in entry["expect"]["rule_refs"]}
    assert any(ref.startswith("MATCH-") for ref in refs), "no cross-document case"
    assert "MH-CHAIN-001" in refs and "MH-CHAIN-002" in refs, "no ownership-gap case"
    assert len(refs) >= 10, sorted(refs)


def test_generation_is_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    assert make_error_set.main(["--out", str(first)]) == 0
    assert make_error_set.main(["--out", str(second)]) == 0

    first_manifest = (first / "_cases.json").read_bytes()
    assert first_manifest == (second / "_cases.json").read_bytes()

    # PDF bytes differ per run (MuPDF embeds a creation timestamp), so
    # determinism is pinned on the rendered text instead.
    names = sorted(path.name for path in first.iterdir() if path.is_dir())
    assert names[0] == "agreement_only"
    assert "control_clean" in names and "control_clean__mr" in names
    sample = "sale_deed_2009.pdf"
    assert _pdf_text(first / "control_clean" / sample) == \
        _pdf_text(second / "control_clean" / sample)
    assert "221/2" in "".join(_pdf_text(first / "control_clean" / sample))
