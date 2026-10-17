#!/usr/bin/env python
"""AC-3 seeded-error corpus generator (Phase 3).

Builds one directory per case under the output root. Each case is a coherent
set of documents **for a single property**: the clean control is internally
consistent (matching identifiers, names, areas, boundaries, a complete
predecessor->buyer ownership chain), and every error case differs from it by
exactly one seeded inconsistency, named in the manifest.

Documents are English (and Marathi, for the three cross-language cases)
text-layer PDFs. The AC-2 report already proves scanned/Marathi *extraction*;
AC-3 measures the consistency/rule/ownership/verdict logic on top of the real
pipeline, so the corpus stays digital-only for speed and determinism. The case
manifest (``_cases.json``) is what ``scripts/ac3_report.py`` scores.

Case manifest shape::

    {
      "name": "survey_mismatch",
      "language": "en",
      "injected": "7/12 extract prints survey number 221/3 instead of 221/2",
      "expect": {"rule_refs": ["MATCH-SURVEY-001"], "verdict": "flagged"},
      "verified_override": {"file.pdf": false},       # optional
      "profile": {"state": "Maharashtra", "survey_number": "221/2", ...},
      "documents": [{"filename": ..., "doc_type": ..., "printed": {...}}]
    }

Usage (from ``backend``)::

    .venv\\Scripts\\python.exe scripts\\make_error_set.py
    .venv\\Scripts\\python.exe scripts\\make_error_set.py --out D:\\tmp\\errset --language en
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

# Reuse the Phase-2 rendering + formatting helpers (same fonts, same date/area
# formats) so the two corpora stay visually and lexically consistent.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_fixtures import area_text, date_text, money, render_digital  # noqa: E402

DEFAULT_OUT = Path.home() / "AppData/Local/Temp/propchain_errorset"

# ---------------------------------------------------------------------------
# The case property. One identity for every case: (english, marathi).
# ---------------------------------------------------------------------------

VILLAGE = ("Wagholi", "वाघोली")
TALUKA = ("Haveli", "हवेली")
DISTRICT = ("Pune", "पुणे")
SURVEY = "221/2"
GAT = "318"
CTS = "148/2"
ULPIN = "PUN-221-2-318"
AREA_SQFT = 2000.0

ROOT_SELLER = ("Dagdu Shinde", "दगडू शिंदे")
MIDDLE = ("Vithal More", "विठ्ठल मोरे")
HOLDER = ("Shantaram Pawar", "शंताराम पवार")

REG_1998 = "MH-PUN-1998-45512"
REG_2009 = "MH-PUN-2009-11223"
REG_MORTGAGE = "MH-PUN-2019-33445"

D_ROOT = date(1998, 4, 20)
D_EXEC = date(2009, 6, 1)
D_REG = date(2009, 6, 15)
D_FERFAR = date(2009, 8, 10)
D_CARD = date(2024, 5, 12)

BOUNDARY_EN = "East: 30 ft DP road; West: Gat No. 318; North: Survey No. 221/2; South: open land"
BOUNDARY_MR = "पूर्व: ३० फूट डी.पी. रस्ता; पश्चिम: गट क्र. 318; उत्तर: स.नं. 221/2; दक्षिण: मोकळी जागा"
BOUNDARY_CHANGED_EN = "East: canal; West: state highway; North: hill slope; South: temple wall"
BOUNDARY_CHANGED_MR = "पूर्व: कालवा; पश्चिम: राज्य महामार्ग; उत्तर: टेकडी; दक्षिण: देवळाची भिंत"


def en_mr(value: tuple[str, str] | str, lang: str) -> str:
    if isinstance(value, str):
        return value
    return value[0] if lang == "en" else value[1]


def honorific(lang: str) -> str:
    return "Shri" if lang == "en" else "श्री"


def row(lang: str, en_label: str, mr_label: str, value: str) -> str:
    return f"{en_label if lang == 'en' else mr_label}: {value}"


# ---------------------------------------------------------------------------
# Document templates
# ---------------------------------------------------------------------------


def sale_deed(
    lang: str,
    *,
    seller: tuple[str, str],
    buyer: tuple[str, str],
    survey: str = SURVEY,
    gat: str = GAT,
    area_sqft: float = AREA_SQFT,
    reg_no: str = REG_2009,
    reg_day: date = D_REG,
    exec_day: date | None = D_EXEC,
    referred_no: str | None = None,
    boundaries: str | None = None,
) -> tuple[list[list[str]], dict]:
    boundary = boundaries or en_mr((BOUNDARY_EN, BOUNDARY_MR), lang)
    lines = [
        "Sale Deed" if lang == "en" else "खरेदीखत",
        row(lang, "Office", "कार्यालय",
            "Office of the Sub-Registrar, Haveli, Pune"
            if lang == "en" else "उप-निबंधक कार्यालय, हवेली, पुणे"),
        row(lang, "Village", "गाव", en_mr(VILLAGE, lang)),
        row(lang, "Taluka", "तालुका", en_mr(TALUKA, lang)),
        row(lang, "District", "जिल्हा", en_mr(DISTRICT, lang)),
        row(lang, "Survey No. / Gat No.", "स.नं. / गट क्र.", f"{survey} / {gat}"),
        row(lang, "Vendor / Seller", "विक्रेता", f"{honorific(lang)} {en_mr(seller, lang)}"),
        row(lang, "Purchaser / Buyer", "खरेदीदार", f"{honorific(lang)} {en_mr(buyer, lang)}"),
        row(lang, "Total Area", "एकूण क्षेत्र", area_text(area_sqft, "sqft", lang)),
        row(lang, "Consideration Amount", "मोबदला रक्कम", money(1250000, lang)),
        row(lang, "Registration No.", "नोंदणी क्रमांक", reg_no),
        row(lang, "Registration Date", "नोंदणी दिनांक", date_text(reg_day, lang, long_form=True)),
    ]
    if exec_day is not None:
        lines.append(
            row(lang, "Date of Execution", "अंमलबजावणी दिनांक", date_text(exec_day, lang))
        )
    lines += [
        "The vendor hereby transfers the property to the purchaser for the consideration"
        if lang == "en" else "विक्रेत्याने ही मालमत्ता खरेदीदारास मोबदल्यासाठी हस्तांतरित केली",
        "received in full; the property is free from encumbrances."
        if lang == "en" else "आहे; मालमत्ता कोणत्याही भारास मुक्त आहे.",
        "Schedule of Property" if lang == "en" else "मालमत्तेचा तपशील",
        row(lang, "Boundaries", "हद्दी", boundary),
    ]
    if referred_no:
        lines.append(
            row(
                lang,
                "Referred Document",
                "संदर्भित दस्तऐवज",
                f"Predecessor Sale Deed No. {referred_no}"
                if lang == "en" else f"पूर्वीचे खरेदीखत क्र. {referred_no}",
            )
        )
    printed = {
        "seller_name": en_mr(seller, lang), "buyer_name": en_mr(buyer, lang),
        "survey_number": survey, "gat_number": gat, "area_sqft": area_sqft,
        "registration_number": reg_no, "registration_date": reg_day.isoformat(),
        "execution_date": exec_day.isoformat() if exec_day else None,
        "boundaries": boundary, "referred_document": referred_no,
    }
    return [lines], printed


def ferfar(
    lang: str,
    *,
    holder: tuple[str, str] = HOLDER,
    reg_no: str = REG_2009,
    mutation_day: date = D_FERFAR,
    entry_no: int = 4212,
) -> tuple[list[list[str]], dict]:
    lines = [
        "Mutation Entry (Ferfar Register)" if lang == "en" else "फेरफार नोंद (फेरफार पत्रक)",
        row(lang, "Village", "गाव", en_mr(VILLAGE, lang)),
        row(lang, "District", "जिल्हा", en_mr(DISTRICT, lang)),
        row(lang, "Survey No.", "स.नं.", SURVEY),
        row(lang, "Purchaser / New Holder", "खरेदीदार", f"{honorific(lang)} {en_mr(holder, lang)}"),
        row(lang, "Total Area", "एकूण क्षेत्र", area_text(AREA_SQFT, "sqft", lang)),
        row(lang, "Sale Deed Registration No.", "खरेदीखत नोंदणी क्रमांक", reg_no),
        row(lang, "Mutation Entry No.", "फेरफार क्र.", str(entry_no)),
        row(lang, "Mutation Date", "फेरफार दिनांक", date_text(mutation_day, lang)),
        "The mutation entry has been certified and the purchaser's name recorded."
        if lang == "en" else "फेरफार प्रमाणित झाला असून खरेदीदाराचे नाव नोंदले आहे.",
    ]
    return [lines], {
        "owner_name": en_mr(holder, lang), "survey_number": SURVEY,
        "registration_number": reg_no, "registration_date": mutation_day.isoformat(),
    }


def record_712(
    lang: str,
    *,
    holder: tuple[str, str] = HOLDER,
    survey: str = SURVEY,
    gat: str = GAT,
    area_sqft: float = AREA_SQFT,
    village: tuple[str, str] = VILLAGE,
) -> tuple[list[list[str]], dict]:
    lines = [
        "7/12 Extract (Record of Rights)" if lang == "en" else "सातबारा उतारा (अधिकार अभिलेख)",
        "Mahabhulekh - Government of Maharashtra"
        if lang == "en" else "महाभूलेख - महाराष्ट्र शासन, भूमी अभिलेख विभाग",
        row(lang, "Village", "गाव", en_mr(village, lang)),
        row(lang, "Taluka", "तालुका", en_mr(TALUKA, lang)),
        row(lang, "District", "जिल्हा", en_mr(DISTRICT, lang)),
        row(lang, "Survey No. / Gat No.", "स.नं. / गट क्र.", f"{survey} / {gat}"),
        row(lang, "Owner / Holder", "धारक व मालक", f"{honorific(lang)} {en_mr(holder, lang)}"),
        row(lang, "Total Area", "एकूण क्षेत्र", area_text(area_sqft, "sqft", lang)),
        row(lang, "Ulpin", "युपिन", ULPIN),
    ]
    return [lines], {
        "owner_name": en_mr(holder, lang), "survey_number": survey, "gat_number": gat,
        "area_sqft": area_sqft, "village": en_mr(village, lang),
    }


def property_card(
    lang: str,
    *,
    holder: tuple[str, str] = HOLDER,
    boundaries: str | None = None,
) -> tuple[list[list[str]], dict]:
    boundary = boundaries or en_mr((BOUNDARY_EN, BOUNDARY_MR), lang)
    lines = [
        "Property Card (City Survey)" if lang == "en" else "मालमत्ता पत्रक (नगर सर्व्हे)",
        row(lang, "Village", "गाव", en_mr(VILLAGE, lang)),
        row(lang, "District", "जिल्हा", en_mr(DISTRICT, lang)),
        row(lang, "CTS No.", "सी.टी.एस. क्र.", CTS),
        row(lang, "Owner's Name", "मालकाचे नाव", f"{honorific(lang)} {en_mr(holder, lang)}"),
        row(lang, "Total Area", "एकूण क्षेत्र", area_text(185.8, "sqm", lang)),
        row(lang, "Boundaries", "हद्दी", boundary),
        row(lang, "Date of Issue", "दिनांक", date_text(D_CARD, lang)),
    ]
    return [lines], {
        "owner_name": en_mr(holder, lang), "cts_number": CTS, "bounds": boundary,
        "area_sqm": 185.8,
    }


def encumbrance_certificate(lang: str) -> tuple[list[list[str]], dict]:
    lines = [
        "Encumbrance Certificate" if lang == "en" else "भारनियमिता दाखला",
        row(lang, "Village", "गाव", en_mr(VILLAGE, lang)),
        row(lang, "District", "जिल्हा", en_mr(DISTRICT, lang)),
        row(lang, "Survey No.", "स.नं.", SURVEY),
        row(lang, "Owner", "मालक", f"{honorific(lang)} {en_mr(HOLDER, lang)}"),
        row(lang, "Total Area", "एकूण क्षेत्र", area_text(AREA_SQFT, "sqft", lang)),
        row(lang, "Search Period", "शोध कालावधी", "01/04/1998 to 31/03/2024"),
        row(lang, "Encumbrance", "भार", "NIL" if lang == "en" else "काही नाही"),
        "Certified that no encumbrance was registered during the search period."
        if lang == "en" else "शोध कालावधीत कोणताही भार नोंदणी झालेला नाही.",
    ]
    return [lines], {"owner_name": en_mr(HOLDER, lang), "survey_number": SURVEY}


def agreement_to_sale(lang: str) -> tuple[list[list[str]], dict]:
    boundary = en_mr((BOUNDARY_EN, BOUNDARY_MR), lang)
    lines = [
        "Agreement to Sale" if lang == "en" else "खरेदीखत करार",
        row(lang, "Village", "गाव", en_mr(VILLAGE, lang)),
        row(lang, "Taluka", "तालुका", en_mr(TALUKA, lang)),
        row(lang, "District", "जिल्हा", en_mr(DISTRICT, lang)),
        row(lang, "Survey No. / Gat No.", "स.नं. / गट क्र.", f"{SURVEY} / {GAT}"),
        row(lang, "Vendor / Seller", "विक्रेता", f"{honorific(lang)} {en_mr(MIDDLE, lang)}"),
        row(lang, "Purchaser / Buyer", "खरेदीदार", f"{honorific(lang)} {en_mr(HOLDER, lang)}"),
        row(lang, "Total Area", "एकूण क्षेत्र", area_text(AREA_SQFT, "sqft", lang)),
        row(lang, "Consideration Amount", "मोबदला रक्कम", money(2250000, lang)),
        row(lang, "Date of Execution", "अंमलबजावणी दिनांक", date_text(D_EXEC, lang)),
        row(lang, "Boundaries", "हद्दी", boundary),
        "This agreement is unregistered; it does not by itself convey title."
        if lang == "en" else "हा करार अ-नोंदणीकृत आहे; यामुळे स्वतःच मालकी हस्तांतरित होत नाही.",
    ]
    return [lines], {
        "seller_name": en_mr(MIDDLE, lang), "buyer_name": en_mr(HOLDER, lang),
        "survey_number": SURVEY, "execution_date": D_EXEC.isoformat(),
    }


def will(lang: str) -> tuple[list[list[str]], dict]:
    lines = [
        "Last Will and Testament" if lang == "en" else "मृत्युपत्र",
        row(lang, "Village", "गाव", en_mr(VILLAGE, lang)),
        row(lang, "District", "जिल्हा", en_mr(DISTRICT, lang)),
        row(lang, "Survey No.", "स.नं.", SURVEY),
        row(lang, "Testator", "मृत्युपत्र करणारे", f"{honorific(lang)} {en_mr(HOLDER, lang)}"),
        row(lang, "Total Area", "एकूण क्षेत्र", area_text(AREA_SQFT, "sqft", lang)),
        row(lang, "Date of Execution", "अंमलबजावणी दिनांक", date_text(date(2020, 1, 5), lang)),
    ]
    return [lines], {"owner_name": en_mr(HOLDER, lang), "survey_number": SURVEY}


def mortgage_deed(lang: str) -> tuple[list[list[str]], dict]:
    lines = [
        "Mortgage Deed" if lang == "en" else "गहाणखत",
        row(lang, "Village", "गाव", en_mr(VILLAGE, lang)),
        row(lang, "Taluka", "तालुका", en_mr(TALUKA, lang)),
        row(lang, "District", "जिल्हा", en_mr(DISTRICT, lang)),
        row(lang, "Survey No. / Gat No.", "स.नं. / गट क्र.", f"{SURVEY} / {GAT}"),
        row(lang, "Mortgagor", "गहाण ठेवणारे", f"{honorific(lang)} {en_mr(HOLDER, lang)}"),
        row(lang, "Mortgagee", "गहाण घेणारे", "Pune Urban Co-operative Bank"
            if lang == "en" else "पुणे अर्बन सहकारी बँक"),
        row(lang, "Total Area", "एकूण क्षेत्र", area_text(AREA_SQFT, "sqft", lang)),
        row(lang, "Registration No.", "नोंदणी क्रमांक", REG_MORTGAGE),
        row(lang, "Registration Date", "नोंदणी दिनांक", date_text(date(2019, 8, 20), lang)),
    ]
    return [lines], {"seller_name": en_mr(HOLDER, lang), "survey_number": SURVEY}


def court_document(lang: str) -> tuple[list[list[str]], dict]:
    lines = [
        "Court Document - Civil Suit" if lang == "en" else "न्यायालयीन दस्तऐवज - दिवाणी दावा",
        "Court: Civil Judge Senior Division, Pune"
        if lang == "en" else "न्यायालय: दिवाणी न्यायाधीश वरिष्ठ स्तर, पुणे",
        row(lang, "Village", "गाव", en_mr(VILLAGE, lang)),
        row(lang, "District", "जिल्हा", en_mr(DISTRICT, lang)),
        row(lang, "Survey No.", "स.नं.", SURVEY),
        row(lang, "Owner", "मालक", f"{honorific(lang)} {en_mr(HOLDER, lang)}"),
        "Suit for injunction concerning the above property; status to be verified."
        if lang == "en" else "वरील मालमत्तेसंबंधी मनाई हुकूमाचा दावा; स्थिती तपासावी.",
    ]
    return [lines], {"owner_name": en_mr(HOLDER, lang), "survey_number": SURVEY}


# ---------------------------------------------------------------------------
# Cases: a base document set + one mutation per error case
# ---------------------------------------------------------------------------

BASE_DOCUMENTS = (
    ("predecessor_sale_deed_1998.pdf", "sale_deed"),
    ("sale_deed_2009.pdf", "sale_deed"),
    ("ferfar_2009.pdf", "ferfar"),
    ("7_12_extract_2024.pdf", "7_12_extract"),
    ("encumbrance_certificate_2024.pdf", "ec"),
    ("property_card_2024.pdf", "property_card"),
)


def base_set(lang: str) -> dict[str, tuple[list[list[str]], dict]]:
    return {
        "predecessor_sale_deed_1998.pdf": sale_deed(
            lang, seller=ROOT_SELLER, buyer=MIDDLE, reg_no=REG_1998,
            reg_day=D_ROOT, exec_day=None,
        ),
        "sale_deed_2009.pdf": sale_deed(
            lang, seller=MIDDLE, buyer=HOLDER, reg_no=REG_2009,
            reg_day=D_REG, exec_day=D_EXEC, referred_no=REG_1998,
        ),
        "ferfar_2009.pdf": ferfar(lang),
        "7_12_extract_2024.pdf": record_712(lang),
        "encumbrance_certificate_2024.pdf": encumbrance_certificate(lang),
        "property_card_2024.pdf": property_card(lang),
    }


def profile() -> dict:
    return {
        "state": "Maharashtra", "district": "Pune", "taluka": "Haveli",
        "village": "Wagholi", "survey_number": SURVEY, "gat_number": GAT,
        "area_sqft": AREA_SQFT,
    }


def _drop(name: str):
    def mutate(docs, lang):
        docs.pop(name, None)
    return mutate


def _agreement_only(docs, lang):
    """The only conveyance is an unregistered agreement: drop the deeds/ferfar."""
    for key in ("predecessor_sale_deed_1998.pdf", "sale_deed_2009.pdf", "ferfar_2009.pdf"):
        docs.pop(key, None)
    docs["agreement_to_sale_2009.pdf"] = agreement_to_sale(lang)


def cases(lang: str) -> list[dict]:
    """(name, injected description, mutation, expected rule refs, verdict?)"""
    return [
        ("control_clean", "nothing: internally consistent control",
         lambda docs, lg: None, [], "verified"),
        ("survey_mismatch", "7/12 extract prints survey number 221/3",
         lambda docs, lg: docs.update({"7_12_extract_2024.pdf": record_712(lg, survey="221/3")}),
         ["MATCH-SURVEY-001"], None),
        ("owner_mismatch", "7/12 extract names a different holder (Baban Kale)",
         lambda docs, lg: docs.update({"7_12_extract_2024.pdf": record_712(lg, holder=("Baban Kale", "बबन काळे"))}),
         ["MATCH-OWNER-001"], None),
        ("area_drift", "2009 sale deed prints 2400 sq ft instead of 2000",
         lambda docs, lg: docs.update({"sale_deed_2009.pdf": sale_deed(
             lg, seller=MIDDLE, buyer=HOLDER, reg_no=REG_2009, reg_day=D_REG,
             exec_day=D_EXEC, referred_no=REG_1998, area_sqft=2400.0)}),
         ["MATCH-AREA-001"], None),
        ("boundary_change", "property card describes different boundaries",
         lambda docs, lg: docs.update({"property_card_2024.pdf": property_card(
             lg, boundaries=en_mr((BOUNDARY_CHANGED_EN, BOUNDARY_CHANGED_MR), lg))}),
         ["MATCH-BOUNDARY-001"], None),
        ("duplicate_registration_number", "1998 deed reuses the 2009 registration number",
         lambda docs, lg: docs.update({"predecessor_sale_deed_1998.pdf": sale_deed(
             lg, seller=ROOT_SELLER, buyer=MIDDLE, reg_no=REG_2009,
             reg_day=D_ROOT, exec_day=None)}),
         ["MATCH-REGNO-001"], None),
        ("date_inversion", "2009 deed is executed after its registration date",
         lambda docs, lg: docs.update({"sale_deed_2009.pdf": sale_deed(
             lg, seller=MIDDLE, buyer=HOLDER, reg_no=REG_2009, reg_day=D_REG,
             exec_day=date(2009, 7, 1), referred_no=REG_1998)}),
         ["MATCH-DATE-001"], None),
        ("predecessor_not_uploaded", "the 1998 predecessor deed is missing from the uploads",
         _drop("predecessor_sale_deed_1998.pdf"), ["MH-CHAIN-001"], "flagged"),
        ("mutation_without_deed", "the ferfar mutation cites a sale deed that was not uploaded",
         _drop("sale_deed_2009.pdf"), ["MH-CHAIN-001"], "flagged"),
        ("mortgage_overlay", "a mortgage deed is added to the uploads",
         lambda docs, lg: docs.update({"mortgage_deed_2019.pdf": mortgage_deed(lg)}),
         ["MH-ENC-001"], None),
        ("will_overlay", "a will is added to the uploads",
         lambda docs, lg: docs.update({"will_2020.pdf": will(lg)}),
         ["MH-SUCC-001"], None),
        ("court_overlay", "a court document is added to the uploads",
         lambda docs, lg: docs.update({"court_case_2021.pdf": court_document(lg)}),
         ["MH-LIT-001"], None),
        ("agreement_only", "the only transfer document is an unregistered agreement to sale",
         _agreement_only, ["MH-CHAIN-002"], None),
        ("profile_identifier_mismatch", "property profile says survey 999/9 (documents 221/2)",
         lambda docs, lg: None, ["MH-IDENT-002"], None),
        ("land_record_missing", "the 7/12 extract is not uploaded",
         _drop("7_12_extract_2024.pdf"), ["MH-LAND-712"], None),
        ("hash_tampered", "one document's stored hash no longer matches (metadata flip)",
         lambda docs, lg: None, ["MH-INTEGRITY-001"], "flagged"),
        ("village_mismatch", "7/12 extract is for a different village (Undri)",
         lambda docs, lg: docs.update({"7_12_extract_2024.pdf": record_712(lg, village=("Undri", "उंड्री"))}),
         ["MATCH-VILLAGE-001"], None),
        ("gat_mismatch", "1998 deed prints Gat No. 512 instead of 318",
         lambda docs, lg: docs.update({"predecessor_sale_deed_1998.pdf": sale_deed(
             lg, seller=ROOT_SELLER, buyer=MIDDLE, reg_no=REG_1998, reg_day=D_ROOT,
             exec_day=None, gat="512")}),
         ["MATCH-GAT-001"], None),
    ]


CASE_PROFILES: dict[str, dict] = {
    "profile_identifier_mismatch": {"survey_number": "999/9"},
}
VERIFIED_OVERRIDES: dict[str, dict[str, bool]] = {
    "hash_tampered": {"sale_deed_2009.pdf": False},
}
#: Cross-language coverage: these cases are generated in Marathi as well.
MR_CASES = ("control_clean", "survey_mismatch", "predecessor_not_uploaded")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output root for the case corpus")
    parser.add_argument("--clean", action="store_true", help="delete the output root first")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_root = Path(args.out)
    if args.clean and out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for lang in ("en", "mr"):
        for name, injected, mutate, expected, verdict in cases(lang):
            if lang == "mr" and name not in MR_CASES:
                continue
            docs = base_set(lang)
            mutate(docs, lang)
            case_name = name if lang == "en" else f"{name}__mr"
            case_dir = out_root / case_name
            case_dir.mkdir(parents=True, exist_ok=True)

            entries = []
            for filename, doc_type in BASE_DOCUMENTS + (
                ("agreement_to_sale_2009.pdf", "agreement_to_sale"),
                ("mortgage_deed_2019.pdf", "mortgage_deed"),
                ("will_2020.pdf", "will"),
                ("court_case_2021.pdf", "court_document"),
            ):
                if filename not in docs:
                    continue
                pages, printed = docs[filename]
                (case_dir / filename).write_bytes(render_digital(pages))
                entries.append({"filename": filename, "doc_type": doc_type, "printed": printed})

            expect = {"rule_refs": expected, "verdict": verdict}
            case_profile = profile() | CASE_PROFILES.get(name, {})
            manifest.append(
                {
                    "name": case_name,
                    "case": name,
                    "language": "marathi" if lang == "mr" else "english",
                    "injected": injected,
                    "expect": expect,
                    "verified_override": VERIFIED_OVERRIDES.get(name, {}),
                    "profile": case_profile,
                    "documents": entries,
                }
            )
            print(f"  {case_name:34} {len(entries)} docs  expect {expected or ['<none>']}")

    (out_root / "_cases.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    total_docs = sum(len(case["documents"]) for case in manifest)
    print(f"\ncases: {len(manifest)}   documents: {total_docs}")
    print(f"manifest: {out_root / '_cases.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
