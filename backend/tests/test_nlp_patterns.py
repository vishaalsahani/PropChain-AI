"""Unit tests for ``app.services.nlp_patterns`` (Phase 2 real NLP engine).

Standalone — no temp-DB fixtures; text blocks mirror the labelled fixtures that
``scripts/make_fixtures.py`` generates (label: value per line, English/Marathi).
"""

import pytest

from app.services.fields import CANONICAL_FIELDS
from app.services.nlp_patterns import PatternNLPExtractor

PAGE_BREAK = "\f"

EN_SALE_DEED = (
    "Sale Deed\n"
    "Office of the Sub-Registrar, Haveli-2, Pune\n"
    "Survey No. / Gat No.: 124/A / 456\n"
    "Vendor / Seller: Shri Suresh Deshmukh\n"
    "Purchaser / Buyer: Smt. Meena Kulkarni\n"
    "Total Area: 1,250 sq.ft\n"
    "Consideration Amount: Rs. 12,50,000/-\n"
    "Registration No.: MH-PUN-2019-12345\n"
    "Registration Date: 15 March 2019\n"
    "Date of Execution: 02/03/2019\n"
    "Boundaries: East: 30 ft road; West: Gat 456\n"
    "Referred Document: Predecessor Sale Deed No. MH-PUN-2004-55667\n"
)

MR_SATBARA = (
    "पृष्ठ एक\n"
    + PAGE_BREAK
    + "सातबारा उतारा (अधिकार अभिलेख)\n"
    "स.नं. / गट क्र.: 124/अ / ४५६\n"
    "धारक व मालक: श्री. सुरेश देशमुख\n"
    "गाव: वाघोली\n"
    "तालुका: हवेली\n"
    "जिल्हा: पुणे\n"
    "एकूण क्षेत्र: १२.५ गुंठा\n"
)


@pytest.fixture(scope="module")
def extractor():
    return PatternNLPExtractor()


def extracted(extractor, doc_type, text):
    return {c.field_name: c.normalized_value for c in extractor.extract(doc_type, text)}


def test_engine_version(extractor):
    assert extractor.engine_version == "patterns-v1"


def test_english_sale_deed_fields(extractor):
    values = extracted(extractor, "sale_deed", EN_SALE_DEED)
    assert values["seller_name"] == "Suresh Deshmukh"
    assert values["buyer_name"] == "Meena Kulkarni"
    assert values["survey_number"] == "124/A"
    assert values["gat_number"] == "456"
    assert values["area"] == "1250"
    assert values["area_unit"] == "sqft"
    assert values["area_sqft"] == "1250"
    assert values["consideration_amount"] == "1250000"
    assert values["registration_number"] == "MH-PUN-2019-12345"
    assert values["registration_date"] == "2019-03-15"
    assert values["execution_date"] == "2019-03-02"
    assert values["boundaries"].startswith("East: 30 ft road")


def test_marathi_satbara_fields_and_page_attribution(extractor):
    candidates = extractor.extract("7_12_extract", MR_SATBARA)
    values = {c.field_name: c.normalized_value for c in candidates}
    assert values["owner_name"] == "सुरेश देशमुख"
    assert values["survey_number"] == "124/अ"
    assert values["gat_number"] == "456"
    assert values["village"] == "वाघोली"
    assert values["taluka"] == "हवेली"
    assert values["district"] == "पुणे"
    assert values["area"] == "12.5"
    assert values["area_unit"] == "guntha"
    assert values["area_sqft"] == "13612.5"
    # All printed rows sit on page 2 (page 1 is a cover stub).
    assert all(candidate.page == 2 for candidate in candidates)


def test_candidates_follow_canonical_field_order(extractor):
    candidates = extractor.extract("sale_deed", EN_SALE_DEED)
    order = [CANONICAL_FIELDS.index(c.field_name) for c in candidates]
    assert order == sorted(order)


def test_snippets_are_trimmed_lines(extractor):
    for candidate in extractor.extract("sale_deed", EN_SALE_DEED):
        assert candidate.snippet and len(candidate.snippet) <= 120
        assert "\n" not in candidate.snippet


def test_standalone_registration_number_when_unlabelled(extractor):
    text = "This deed was registered at the office; entry MH-PUN-2021-44556 was certified."
    values = extracted(extractor, "ferfar", text)
    assert values["registration_number"] == "MH-PUN-2021-44556"


def test_standalone_marked_date(extractor):
    # No "नोंदणी दिनांक" label, but the line has दिनांक + नोंदणी markers.
    values = extracted(extractor, "ec", "दिनांक 07/08/2020 रोजी नोंदणी झाली.")
    assert values["registration_date"] == "2020-08-07"


def test_area_in_square_yards_is_converted(extractor):
    values = extracted(extractor, "property_card", "CTS No.: CTS 1234\nTotal Area: 500 sq.yd")
    assert values["area"] == "4500"
    assert values["area_unit"] == "sqft"
    assert values["area_sqft"] == "4500"
    assert values["cts_number"] == "1234"


def test_garbage_text_yields_nothing(extractor):
    assert extractor.extract("sale_deed", "lorem ipsum dolor sit amet 12345") == []
    assert extractor.extract("7_12_extract", "") == []


def test_no_fabrication_on_empty_or_invalid_values(extractor):
    # Label present, value absent.
    assert extractor.extract("7_12_extract", "धारक व मालक:") == []
    # Label present, value is not a plausible name (digits only).
    assert extractor.extract("sale_deed", "Vendor: 12345") == []
    # Label present, value is not a date.
    assert extracted(extractor, "sale_deed", "Registration Date: not a date") == {}


def test_unknown_doc_type_uses_generic_sweep(extractor):
    text = "Owner's Name: Rajesh Patil\nVillage: Wagholi\nSurvey No.: 56/2"
    values = extracted(extractor, "unknown", text)
    assert values["owner_name"] == "Rajesh Patil"
    assert values["village"] == "Wagholi"
    assert values["survey_number"] == "56/2"


def test_doc_type_specific_labels(extractor):
    gift = extracted(extractor, "gift_deed", "Donor: Shri Anil Jadhav\nDonee: Smt. Kavita Pawar")
    assert gift["seller_name"] == "Anil Jadhav"
    assert gift["buyer_name"] == "Kavita Pawar"

    will = extracted(extractor, "will", "Testator: Shri Dattatray Bhosale\nVillage: Undri")
    assert will["owner_name"] == "Dattatray Bhosale"
    assert will["village"] == "Undri"
