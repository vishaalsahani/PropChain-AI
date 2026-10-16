"""Unit tests for ``app.services.normalize`` (Phase 2 extraction normalization).

Standalone — no temp-DB fixtures; these are pure functions.
"""

from app.services import normalize as N


# --------------------------------------------------------------------------
# Digits / whitespace
# --------------------------------------------------------------------------


def test_devanagari_digits_fold():
    assert N.devanagari_digits_to_ascii("१२४/अ") == "124/अ"
    assert N.devanagari_digits_to_ascii("१२.५") == "12.5"
    assert N.devanagari_digits_to_ascii("no digits") == "no digits"


def test_normalize_whitespace():
    assert N.normalize_whitespace("  a\t b\n\n c ") == "a b c"
    assert N.normalize_whitespace(None) == ""


# --------------------------------------------------------------------------
# Names
# --------------------------------------------------------------------------


def test_strip_honorifics_english_and_marathi():
    assert N.strip_honorifics("Shri Suresh Deshmukh") == "Suresh Deshmukh"
    assert N.strip_honorifics("Smt. Meena Kulkarni") == "Meena Kulkarni"
    assert N.strip_honorifics("श्री. सुरेश देशमुख") == "सुरेश देशमुख"
    assert N.strip_honorifics("श्रीमती मीना कुलकर्णी") == "मीना कुलकर्णी"
    assert N.strip_honorifics("Rajesh Patil") == "Rajesh Patil"


def test_normalize_person_key():
    assert N.normalize_person_key("Shri Suresh  Deshmukh.") == "suresh deshmukh"
    assert N.normalize_person_key("श्री. सुरेश देशमुख") == "सुरेश देशमुख"


def test_name_similarity_ignores_honorifics_and_case():
    # Different scripts share only spaces, so similarity stays tiny but not 0.
    assert N.name_similarity("Shri Suresh Deshmukh", "सुरेश देशमुख") < 20.0
    assert N.name_similarity("Smt. Meena Kulkarni", "MEENA KULKARNI") >= 99.0
    assert N.name_similarity("Suresh Deshmukh", "Rajesh Patil") < 75.0
    assert N.name_similarity("", "Rajesh Patil") == 0.0


# --------------------------------------------------------------------------
# Amounts
# --------------------------------------------------------------------------


def test_parse_amount_indian_grouping_and_markers():
    assert N.parse_amount("Rs. 12,50,000/-") == 1250000.0
    assert N.parse_amount("₹१२,५०,०००/-") == 1250000.0
    assert N.parse_amount("Consideration Amount: Rs. 8,75,000/-") == 875000.0
    assert N.parse_amount("no money here") is None


def test_parse_amount_multipliers():
    assert N.parse_amount("12.5 लाख") == 1250000.0
    assert N.parse_amount("1.2 करोड") == 12000000.0
    assert N.parse_amount("Rs. 45 lakh") == 4500000.0


# --------------------------------------------------------------------------
# Areas
# --------------------------------------------------------------------------


def test_parse_area_value_and_unit_forms():
    assert N.parse_area("एकूण क्षेत्र: १२.५ गुंठा") == (12.5, "guntha")
    assert N.parse_area("Total Area 1,250 sq.ft") == (1250.0, "sqft")
    assert N.parse_area("78.25 sq.m") == (78.25, "sqm")
    assert N.parse_area("area 0.40 हे.आर.") == (0.4, "hectare")
    assert N.parse_area("2.5 acres") == (2.5, "acre")
    assert N.parse_area("no area printed") is None


def test_parse_area_unit_before_value():
    assert N.parse_area("गुंठा : 24.7") == (24.7, "guntha")


def test_to_sqft_conversions_exact():
    assert N.to_sqft(1250.0, "sqft") == 1250.0
    assert N.to_sqft(12.5, "guntha") == 13612.5
    assert N.to_sqft(1.0, "acre") == 43560.0
    assert N.to_sqft(0.4, "hectare") == 0.4 * 107639.0
    assert N.to_sqft(10.0, "sqm") == 107.639
    assert N.to_sqft(10.0, "furlong") is None


def test_canonicalize_area_maps_sqyd_to_sqft():
    assert N.canonicalize_area(500.0, "sqyd") == (4500.0, "sqft")
    assert N.canonicalize_area(12.5, "guntha") == (12.5, "guntha")
    assert N.canonicalize_area(1.0, "furlong") is None


# --------------------------------------------------------------------------
# Dates
# --------------------------------------------------------------------------


def test_parse_iso_date_formats():
    assert N.parse_iso_date("15/03/2019") == "2019-03-15"
    assert N.parse_iso_date("15-03-2019") == "2019-03-15"
    assert N.parse_iso_date("15.03.2019") == "2019-03-15"
    assert N.parse_iso_date("2019-03-15") == "2019-03-15"
    assert N.parse_iso_date("15 March 2019") == "2019-03-15"
    assert N.parse_iso_date("15th March 2019") == "2019-03-15"
    assert N.parse_iso_date("March 15, 2019") == "2019-03-15"


def test_parse_iso_date_marathi_and_devanagari_digits():
    assert N.parse_iso_date("१५ मार्च २०१९") == "2019-03-15"
    assert N.parse_iso_date("नोंदणी दिनांक: ०२/०३/२०१९") == "2019-03-02"


def test_parse_iso_date_two_digit_years():
    assert N.parse_iso_date("15/03/19") == "2019-03-15"
    assert N.parse_iso_date("15/03/99") == "1999-03-15"


def test_parse_iso_date_rejects_impossible_dates():
    assert N.parse_iso_date("31/02/2019") is None
    assert N.parse_iso_date("13/13/2019") is None
    assert N.parse_iso_date("no date here") is None


def test_parse_iso_date_unambiguous_mm_dd_pair_swaps():
    assert N.parse_iso_date("05/13/2019") == "2019-05-13"


# --------------------------------------------------------------------------
# Identifiers
# --------------------------------------------------------------------------


def test_normalize_identifier():
    assert N.normalize_identifier("124 / अ") == "124/अ"
    assert N.normalize_identifier("56 / 2b") == "56/2B"
    assert N.normalize_identifier("४५६") == "456"


def test_normalize_registration_number():
    assert N.normalize_registration_number("mh-pun-2019-12345") == "MH-PUN-2019-12345"
    assert N.normalize_registration_number("MH PUN 2019 12345") == "MHPUN201912345"


def test_script_profile():
    assert N.script_profile("सुरेश abc") == (5, 3)
    assert N.script_profile("") == (0, 0)
