#!/usr/bin/env python
"""Deterministic labelled-fixture generator for the Phase 2 / AC-2 harness.

Writes 18 fictional Maharashtra property documents (8 document types x
{English, Marathi} plus one ``.jpg`` and one ``.png`` image extra) with a
ground-truth ``<stem>.json`` next to every fixture and a ``_manifest.json``.

Variants
--------
``digital``
    PDF with a real, correctly extracted text layer (drawn with the Mangal TTF
    via ``Page.insert_text``).  Devanagari is *unshaped* on this path (PyMuPDF
    has no HarfBuzz here), which is why the visible quality is secondary: the
    pipeline reads the text layer, and it is exact.
``scanned``
    The same page laid out by MuPDF's HTML shaper (correct Devanagari glyphs),
    rasterised at 200 dpi, rotated by a seeded +/-0.4-2.0 degrees, given seeded
    mild Gaussian noise and JPEG q=70, then embedded as an image page (or saved
    as the bare ``.jpg``/``.png`` extras).  No text layer — that is the point.

The generators use the same label wording as the extractor's pattern packs
("Vendor / Seller", "मोबदला रक्कम", "नोंदणी दिनांक", ...).  This is a
deliberate prototype compromise: the corpus measures the end-to-end pipeline
(render -> OCR -> classify -> extract -> normalize) on realistic layouts, not
generalisation to unseen wording.  Phase 10 (spec AC dataset) replaces it.

Usage
-----
    .venv\\Scripts\\python.exe scripts\\make_fixtures.py
    .venv\\Scripts\\python.exe scripts\\make_fixtures.py --out DIR --seed 42
"""

from __future__ import annotations

import argparse
import html
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import cv2
import numpy as np
import pymupdf

#: Area-unit -> square-feet factor. Must stay in sync with app.services.normalize.
AREA_TO_SQFT: dict[str, float] = {
    "sqft": 1.0,
    "sqyd": 9.0,
    "sqm": 10.7639,
    "guntha": 1089.0,
    "acre": 43560.0,
    "hectare": 107639.0,
}

FONT_FILE = Path(r"C:\Windows\Fonts\mangal.ttf")
#: MuPDF 1.28.2 resolves a plain path but not the file:/// URL form.
FONT_URL = str(FONT_FILE).replace("\\", "/")

A4_W, A4_H = 595.276, 841.89
MARGIN = 50.0
LINE_H = 18.0
SCAN_DPI = 200
JPEG_QUALITY = 70

DEVA_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
MONTHS_EN = ("January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December")
MONTHS_MR = ("जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून", "जुलै",
             "ऑगस्ट", "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर")

LANGS = ("en", "mr")
DOC_TYPE_ORDER = ("sale_deed", "agreement_to_sale", "gift_deed", "7_12_extract",
                  "8a_record", "ferfar", "property_card", "ec")

#: (english, marathi) pools — realistic Maharashtra names/places.
NAMES = (
    ("Rajesh Patil", "राजेश पाटील"),
    ("Suresh Deshmukh", "सुरेश देशमुख"),
    ("Anil Jadhav", "अनिल जाधव"),
    ("Meena Kulkarni", "मीना कुलकर्णी"),
    ("Vijay Shinde", "विजय शिंदे"),
    ("Sunita More", "सुनीता मोरे"),
    ("Prakash Gaikwad", "प्रकाश गायकवाड"),
    ("Kavita Pawar", "कविता पवार"),
    ("Dattatray Bhosale", "दत्तात्रय भोसले"),
    ("Nilesh Chavan", "निलेश चव्हाण"),
    ("Ashwini Jagtap", "अश्विनी जगताप"),
    ("Mahesh Sawant", "महेश सावंत"),
)
VILLAGES = (("Wagholi", "वाघोली"), ("Kharadi", "खराडी"), ("Hinjawadi", "हिंजवडी"),
            ("Baner", "बाणेर"), ("Wakad", "वाकड"), ("Undri", "उंड्री"),
            ("Manjri", "मांजरी"), ("Talegaon", "तळेगाव"))
TALUKAS = (("Haveli", "हवेली"), ("Mulshi", "मुळशी"), ("Khed", "खेड"),
           ("Shirur", "शिरूर"), ("Maval", "मावळ"))
DISTRICTS = (("Pune", "पुणे"), ("Satara", "सातारा"), ("Nashik", "नाशिक"))
SURVEYS = ("124/A", "56/2", "37/1A", "78/3", "145/2A", "92", "33/1B", "267/4")
GATS = ("456", "78", "210/2", "512", "96", "341")
CTS_NUMBERS = ("CTS 1234", "CTS 567", "CTS 148/2", "CTS 902")
UNIT_TEXT = {
    "en": {"sqft": "sq.ft", "sqyd": "sq.yd", "sqm": "sq.m",
           "guntha": "guntha", "hectare": "hectare", "acre": "acre"},
    "mr": {"sqft": "चौ.फूट", "sqyd": "चौ.गज", "sqm": "चौ.मी.",
           "guntha": "गुंठा", "hectare": "हेक्टर", "acre": "एकर"},
}
UNIT_POOLS: dict[str, tuple[float, ...]] = {
    "sqft": (820.0, 950.0, 1250.0, 1450.0),
    "sqyd": (750.0, 950.0, 1100.0),
    "sqm": (45.0, 62.5, 78.25),
    "guntha": (10.0, 12.5, 24.7),
    "hectare": (0.247, 0.405, 0.607),
    "acre": (0.75, 1.25, 2.5),
}
UNIT_DECIMALS = {"sqft": 0, "sqyd": 0, "sqm": 2, "guntha": 2, "hectare": 3, "acre": 2}
MONEY = (12_50_000, 8_75_000, 45_00_000, 22_50_000, 35_00_000, 18_00_000, 62_00_000)


def deva(text: str) -> str:
    """Latin digits -> Devanagari digits."""
    return str(text).translate(DEVA_DIGITS)


def inr_group(amount: int) -> str:
    """Indian digit grouping: 1250000 -> '12,50,000'."""
    digits = str(int(amount))
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    parts: list[str] = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def money(amount: int, lang: str) -> str:
    group = inr_group(amount)
    return f"₹{deva(group)}/-" if lang == "mr" else f"Rs. {group}/-"


def area_text(value: float, unit: str, lang: str) -> str:
    number = f"{value:,.{UNIT_DECIMALS[unit]}f}"
    if lang == "mr":
        number = deva(number)
    return f"{number} {UNIT_TEXT[lang][unit]}"


def date_text(day: date, lang: str, long_form: bool = False) -> str:
    if long_form:
        if lang == "mr":
            return f"{deva(str(day.day))} {MONTHS_MR[day.month - 1]} {deva(str(day.year))}"
        return f"{day.day} {MONTHS_EN[day.month - 1]} {day.year}"
    text = f"{day.day:02d}/{day.month:02d}/{day.year}"
    return deva(text) if lang == "mr" else text


class Doc:
    """Fixture under construction: pages of text lines + ground truth."""

    def __init__(self, doc_type: str, lang: str, variant: str, filename: str) -> None:
        self.doc_type = doc_type
        self.lang = lang
        self.variant = variant
        self.filename = filename
        self.pages: list[list[str]] = [[]]
        self.expected: dict[str, object] = {}
        self.tokens: list[str] = []
        self.notes: list[str] = []

    def line(self, text: str) -> None:
        self.pages[-1].append(text)

    def new_page(self) -> None:
        self.pages.append([])

    def gt(self, field: str, value: object, token: str | None = None) -> None:
        self.expected[field] = value
        if token is not None:
            self.tokens.append(token)

    def gt_row(self, field: str, label: str, value: str) -> None:
        """Printed 'label: value' row that is also ground truth."""
        self.line(f"{label}: {value}")
        self.gt(field, value, token=value)


def pick(rng: random.Random, pool):
    return pool[rng.randrange(len(pool))]


def name_pair(rng: random.Random, exclude: tuple[str, str] | None = None) -> tuple[str, str]:
    pair = pick(rng, NAMES)
    while exclude is not None and pair == exclude:
        pair = pick(rng, NAMES)
    return pair


def title_row(doc: Doc, en: str, mr: str) -> None:
    doc.line(en if doc.lang == "en" else mr)


def add_area(doc: Doc, rng: random.Random, unit: str) -> None:
    value = pick(rng, UNIT_POOLS[unit])
    printed = area_text(value, unit, doc.lang)
    doc.gt_row("area", "Total Area" if doc.lang == "en" else "एकूण क्षेत्र", printed)
    doc.gt("area_unit", unit)
    doc.gt("area_sqft", round(value * AREA_TO_SQFT[unit], 2))


def add_registration(doc: Doc, rng: random.Random, reg_no: str, reg_day: date,
                     exec_day: date | None = None) -> None:
    doc.line(f"{'Registration No.' if doc.lang == 'en' else 'नोंदणी क्रमांक'}: {reg_no}")
    doc.gt("registration_number", reg_no, token=reg_no)
    label = "Registration Date" if doc.lang == "en" else "नोंदणी दिनांक"
    printed = date_text(reg_day, doc.lang, long_form=True)
    doc.line(f"{label}: {printed}")
    doc.gt("registration_date", reg_day.isoformat(), token=printed)
    if exec_day is not None:
        exec_label = "Date of Execution" if doc.lang == "en" else "अंमलबजावणी दिनांक"
        exec_printed = date_text(exec_day, doc.lang)
        doc.line(f"{exec_label}: {exec_printed}")
        doc.gt("execution_date", exec_day.isoformat(), token=exec_printed)


def build_sale_deed(doc: Doc, rng: random.Random) -> None:
    seller = name_pair(rng)
    buyer = name_pair(rng, exclude=seller)
    village, taluka, district = pick(rng, VILLAGES), pick(rng, TALUKAS), pick(rng, DISTRICTS)
    survey, gat = pick(rng, SURVEYS), pick(rng, GATS)
    amount = pick(rng, MONEY)
    reg_day = date(rng.randint(2015, 2023), rng.randint(1, 12), rng.randint(1, 28))
    exec_day = reg_day - timedelta(days=rng.randint(7, 40))
    reg_no = f"MH-PUN-{reg_day.year}-{rng.randint(10000, 99999)}"
    prev_no = f"MH-PUN-{reg_day.year - 15}-{rng.randint(10000, 99999)}"

    mr = doc.lang == "mr"
    seller_name = seller[1] if mr else seller[0]
    buyer_name = buyer[1] if mr else buyer[0]
    honorific_s = "श्री" if mr else "Shri"
    honorific_b = "श्रीमती" if mr else "Smt."
    # A deed names the parties (vendor/purchaser), not an "owner": owner_name is
    # deliberately not ground truth here (there is no owner label to extract).
    doc.gt("seller_name", seller_name)
    doc.gt("buyer_name", buyer_name)
    doc.gt("survey_number", survey, token=survey)
    doc.gt("gat_number", gat, token=gat)
    doc.gt("consideration_amount", float(amount))
    doc.gt("currency", "INR")
    doc.notes.append("Deed names the parties only: seller_name/buyer_name are the parties; "
                     "no owner_name label is printed.")

    title_row(doc, "Sale Deed", "खरेदीखत")
    doc.line(("Office of the Sub-Registrar, " + taluka[0] + ", " + district[0]) if not mr
             else ("उप-निबंधक कार्यालय, " + taluka[1] + ", " + district[1]))
    doc.gt_row("village", "Village" if not mr else "गाव", village[1] if mr else village[0])
    doc.gt_row("taluka", "Taluka" if not mr else "तालुका", taluka[1] if mr else taluka[0])
    doc.gt_row("district", "District" if not mr else "जिल्हा", district[1] if mr else district[0])
    doc.line(f"{'Survey No. / Gat No.' if not mr else 'स.नं. / गट क्र.'}: {survey} / {gat}")
    doc.line(f"{'Vendor / Seller' if not mr else 'विक्रेता'}: {honorific_s} {seller_name}")
    doc.line(f"{'Purchaser / Buyer' if not mr else 'खरेदीदार'}: {honorific_b} {buyer_name}")
    add_area(doc, rng, "sqft")
    amount_printed = money(amount, doc.lang)
    doc.line(f"{'Consideration Amount' if not mr else 'मोबदला रक्कम'}: {amount_printed}")
    doc.gt("consideration_amount", float(amount), token=amount_printed)
    add_registration(doc, rng, reg_no, reg_day, exec_day)
    doc.line("The vendor hereby transfers the property to the purchaser for the total"
             if not mr else "विक्रेत्याने ही मालमत्ता खरेदीदारास एकूण मोबदल्यासाठी हस्तांतरित केली")
    doc.line("consideration received in full; the property is free from encumbrances."
             if not mr else "आहे; मालमत्ता कोणत्याही भारास मुक्त आहे.")

    doc.new_page()
    doc.line("Schedule of Property" if not mr else "मालमत्तेचा तपशील")
    boundary = (f"East: 30 ft DP road; West: Gat No. {gat}; North: Survey No. {survey}; South: open land"
                if not mr else
                f"पूर्व: ३० फूट डी.पी. रस्ता; पश्चिम: गट क्र. {gat}; उत्तर: स.नं. {survey}; दक्षिण: मोकळी जागा")
    doc.gt_row("boundaries", "Boundaries" if not mr else "हद्दी", boundary)
    doc.gt_row("referred_document", "Referred Document" if not mr else "संदर्भित दस्तऐवज",
               f"Predecessor Sale Deed No. {prev_no}" if not mr else f"पूर्वीचे खरेदीखत क्र. {prev_no}")
    doc.line("Possession has been handed over on the date of execution."
             if not mr else "ताबा अंमलबजावणीच्या दिनांकास देण्यात आला आहे.")


def build_agreement_to_sale(doc: Doc, rng: random.Random) -> None:
    seller = name_pair(rng)
    buyer = name_pair(rng, exclude=seller)
    village, taluka, district = pick(rng, VILLAGES), pick(rng, TALUKAS), pick(rng, DISTRICTS)
    survey, gat = pick(rng, SURVEYS), pick(rng, GATS)
    amount = pick(rng, MONEY)
    exec_day = date(rng.randint(2015, 2023), rng.randint(1, 12), rng.randint(1, 28))
    mr = doc.lang == "mr"
    seller_name = seller[1] if mr else seller[0]
    buyer_name = buyer[1] if mr else buyer[0]

    # An agreement names the parties, not an owner: owner_name is not ground truth.
    doc.gt("seller_name", seller_name)
    doc.gt("buyer_name", buyer_name)
    doc.gt("survey_number", survey, token=survey)
    doc.gt("gat_number", gat, token=gat)
    doc.gt("consideration_amount", float(amount))
    doc.gt("currency", "INR")
    doc.notes.append("Agreement is unregistered: no registration number/date by design; "
                     "owner_name not printed (parties only).")

    title_row(doc, "Agreement to Sale", "विक्री करारनामा")
    doc.gt_row("village", "Village" if not mr else "गाव", village[1] if mr else village[0])
    doc.gt_row("taluka", "Taluka" if not mr else "तालुका", taluka[1] if mr else taluka[0])
    doc.gt_row("district", "District" if not mr else "जिल्हा", district[1] if mr else district[0])
    doc.line(f"{'Survey No. / Gat No.' if not mr else 'स.नं. / गट क्र.'}: {survey} / {gat}")
    doc.line(f"{'Vendor / Seller' if not mr else 'विक्रेता'}: {'Shri' if not mr else 'श्री'} {seller_name}")
    doc.line(f"{'Purchaser / Buyer' if not mr else 'खरेदीदार'}: {'Smt.' if not mr else 'श्रीमती'} {buyer_name}")
    add_area(doc, rng, "sqft")
    total_printed = money(amount, doc.lang)
    doc.line(f"{'Total Consideration' if not mr else 'एकूण मोबदला'}: {total_printed}")
    doc.gt("consideration_amount", float(amount), token=total_printed)
    exec_printed = date_text(exec_day, doc.lang)
    doc.line(f"{'Date of Execution' if not mr else 'अंमलबजावणी दिनांक'}: {exec_printed}")
    doc.gt("execution_date", exec_day.isoformat(), token=exec_printed)
    doc.line("The sale deed shall be executed within six months from this date."
             if not mr else "या दिनांकापासून सहा महिन्यांत खरेदीखत करून देणे बंधनकारक आहे.")


def build_gift_deed(doc: Doc, rng: random.Random) -> None:
    donor = name_pair(rng)
    donee = name_pair(rng, exclude=donor)
    survey = pick(rng, SURVEYS)
    village, taluka, district = pick(rng, VILLAGES), pick(rng, TALUKAS), pick(rng, DISTRICTS)
    nominal = 51_000
    reg_day = date(rng.randint(2015, 2023), rng.randint(1, 12), rng.randint(1, 28))
    exec_day = reg_day - timedelta(days=rng.randint(5, 30))
    reg_no = f"MH-PUN-{reg_day.year}-{rng.randint(10000, 99999)}"
    mr = doc.lang == "mr"
    donor_name = donor[1] if mr else donor[0]
    donee_name = donee[1] if mr else donee[0]

    # A gift deed names donor/donee, not an "owner": owner_name not ground truth.
    doc.gt("seller_name", donor_name)
    doc.gt("buyer_name", donee_name)
    doc.gt("survey_number", survey, token=survey)
    doc.gt("consideration_amount", float(nominal))
    doc.gt("currency", "INR")
    doc.notes.append("No donor/donee fields in the canonical vocabulary: seller_name = donor, "
                     "buyer_name = donee. Area printed in sq.yd (converted to sq.ft).")

    title_row(doc, "Gift Deed", "बक्षीसपत्र (गिफ्ट डीड)")
    doc.gt_row("village", "Village" if not mr else "गाव", village[1] if mr else village[0])
    doc.gt_row("taluka", "Taluka" if not mr else "तालुका", taluka[1] if mr else taluka[0])
    doc.gt_row("district", "District" if not mr else "जिल्हा", district[1] if mr else district[0])
    doc.gt_row("survey_number", "Survey No." if not mr else "स.नं.", survey)
    doc.line(f"{'Donor' if not mr else 'देणगीदार'}: {'Shri' if not mr else 'श्री'} {donor_name}")
    doc.line(f"{'Donee' if not mr else 'देणी घेणारा'}: {'Smt.' if not mr else 'श्रीमती'} {donee_name}")
    add_area(doc, rng, "sqyd")
    nominal_printed = money(nominal, doc.lang)
    doc.line(f"{'Nominal Consideration' if not mr else 'प्रतीक रक्कम'}: {nominal_printed}")
    doc.gt("consideration_amount", float(nominal), token=nominal_printed)
    add_registration(doc, rng, reg_no, reg_day, exec_day)
    doc.line("The donor out of natural love and affection gifts the property to the donee."
             if not mr else "देणगीदाराने नैसर्गिक प्रेमापोटी ही मालमत्ता देणी घेणाऱ्यास बक्षीस दिली आहे.")


def build_7_12_extract(doc: Doc, rng: random.Random) -> None:
    owner = name_pair(rng)
    village, taluka, district = pick(rng, VILLAGES), pick(rng, TALUKAS), pick(rng, DISTRICTS)
    survey, gat = pick(rng, SURVEYS), pick(rng, GATS)
    unit = "guntha" if doc.lang == "en" else "hectare"
    issue_day = date(rng.randint(2019, 2024), rng.randint(1, 12), rng.randint(1, 28))
    mr = doc.lang == "mr"
    owner_name = owner[1] if mr else owner[0]

    doc.gt("owner_name", owner_name)
    doc.gt("survey_number", survey, token=survey)
    doc.gt("gat_number", gat, token=gat)
    doc.notes.append("7/12 extract: the printed 'Extract Date' is an issue date, deliberately "
                     "not ground truth; there is no registration date on this document.")

    title_row(doc, "7/12 Extract (Record of Rights)", "सातबारा उतारा (अधिकार अभिलेख)")
    doc.line("Mahabhulekh - Government of Maharashtra" if not mr
             else "महाभूलेख - महाराष्ट्र शासन, भूमी अभिलेख विभाग")
    doc.gt_row("village", "Village" if not mr else "गाव", village[1] if mr else village[0])
    doc.gt_row("taluka", "Taluka" if not mr else "तालुका", taluka[1] if mr else taluka[0])
    doc.gt_row("district", "District" if not mr else "जिल्हा", district[1] if mr else district[0])
    doc.line(f"{'Survey No. / Gat No.' if not mr else 'स.नं. / गट क्र.'}: {survey} / {gat}")
    doc.line(f"{'Owner / Holder' if not mr else 'धारक व मालक'}: "
             f"{'Shri' if not mr else 'श्री'} {owner_name}")
    add_area(doc, rng, unit)
    doc.line(f"{'Extract Date' if not mr else 'उतारा दिनांक'}: {date_text(issue_day, doc.lang)}")
    doc.line("This extract is issued for information only; it confers no right or title."
             if not mr else "हा उतारा केवळ माहितीसाठी आहे; यामुळे कोणताही हक्क प्राप्त होत नाही.")


def build_8a_record(doc: Doc, rng: random.Random) -> None:
    holder = name_pair(rng)
    village, taluka, district = pick(rng, VILLAGES), pick(rng, TALUKAS), pick(rng, DISTRICTS)
    survey = pick(rng, SURVEYS)
    issue_day = date(rng.randint(2019, 2024), rng.randint(1, 12), rng.randint(1, 28))
    mr = doc.lang == "mr"
    holder_name = holder[1] if mr else holder[0]

    doc.gt("owner_name", holder_name)
    doc.gt("survey_number", survey, token=survey)
    doc.notes.append("8A record: holder only; no Gat number, no registration date printed.")

    title_row(doc, "8A Record (Other Rights)", "नमुना आठ-अ उतारा (इतर हक्क)")
    doc.gt_row("village", "Village" if not mr else "गाव", village[1] if mr else village[0])
    doc.gt_row("taluka", "Taluka" if not mr else "तालुका", taluka[1] if mr else taluka[0])
    doc.gt_row("district", "District" if not mr else "जिल्हा", district[1] if mr else district[0])
    doc.gt_row("survey_number", "Survey No." if not mr else "स.नं.", survey)
    doc.line(f"{'Holder' if not mr else 'खातेदार'}: {'Shri' if not mr else 'श्री'} {holder_name}")
    add_area(doc, rng, "hectare")
    doc.line(f"{'Extract Date' if not mr else 'उतारा दिनांक'}: {date_text(issue_day, doc.lang, True)}")
    doc.line("The above entry has been recorded in the record of rights of the village."
             if not mr else "वरील नोंद गावाच्या अधिकार अभिलेखात नोंदविण्यात आली आहे.")


def build_ferfar(doc: Doc, rng: random.Random) -> None:
    buyer = name_pair(rng)
    village, district = pick(rng, VILLAGES), pick(rng, DISTRICTS)
    survey = pick(rng, SURVEYS)
    unit = "acre" if doc.lang == "en" else "guntha"
    mut_day = date(rng.randint(2015, 2023), rng.randint(1, 12), rng.randint(1, 28))
    reg_no = f"MH-PUN-{mut_day.year}-{rng.randint(10000, 99999)}"
    entry_no = rng.randint(100, 999)
    mr = doc.lang == "mr"
    buyer_name = buyer[1] if mr else buyer[0]

    doc.gt("owner_name", buyer_name)
    doc.gt("survey_number", survey, token=survey)
    doc.gt("registration_number", reg_no, token=reg_no)
    doc.gt("registration_date", mut_day.isoformat(), token=date_text(mut_day, doc.lang))
    doc.notes.append("ferfar: registration_date is the mutation (ferfar) entry date; the "
                     "registration number is the referenced sale deed.")

    title_row(doc, "Mutation Entry (Ferfar Register)", "फेरफार नोंद (फेरफार पत्रक)")
    doc.gt_row("village", "Village" if not mr else "गाव", village[1] if mr else village[0])
    doc.gt_row("district", "District" if not mr else "जिल्हा", district[1] if mr else district[0])
    doc.gt_row("survey_number", "Survey No." if not mr else "स.नं.", survey)
    doc.line(f"{'Purchaser / New Holder' if not mr else 'खरेदीदार'} / "
             f"{'Holder' if not mr else 'धारक'}: {'Shri' if not mr else 'श्री'} {buyer_name}")
    add_area(doc, rng, unit)
    reg_label = "Sale Deed Registration No." if not mr else "खरेदीखत नोंदणी क्रमांक"
    doc.line(f"{reg_label}: {reg_no}")
    doc.gt("registration_number", reg_no, token=reg_no)
    doc.line(f"{'Mutation Entry No.' if not mr else 'फेरफार क्र.'}: "
             f"{deva(str(entry_no)) if mr else entry_no}")
    mut_printed = date_text(mut_day, doc.lang)
    doc.line(f"{'Mutation Date' if not mr else 'फेरफार दिनांक'}: {mut_printed}")
    doc.gt("registration_date", mut_day.isoformat(), token=mut_printed)
    doc.line("The mutation entry has been certified and the purchaser's name entered."
             if not mr else "फेरफार प्रमाणित झाला असून खरेदीदाराचे नाव अधिकार अभिलेखात नोंदले आहे.")


def build_property_card(doc: Doc, rng: random.Random) -> None:
    owner = name_pair(rng)
    village, district = pick(rng, VILLAGES), pick(rng, DISTRICTS)
    cts = pick(rng, CTS_NUMBERS)
    issue_day = date(rng.randint(2018, 2024), rng.randint(1, 12), rng.randint(1, 28))
    mr = doc.lang == "mr"
    owner_name = owner[1] if mr else owner[0]

    doc.gt("owner_name", owner_name)
    doc.gt("cts_number", cts.split()[-1], token=cts)
    doc.notes.append("Property card: city-survey record; CTS number instead of survey number, "
                     "no registration date.")

    title_row(doc, "Property Card (City Survey)", "मालमत्ता पत्रक (नगर सर्व्हे)")
    doc.gt_row("village", "Village" if not mr else "गाव", village[1] if mr else village[0])
    doc.gt_row("district", "District" if not mr else "जिल्हा", district[1] if mr else district[0])
    doc.line(f"{'CTS No.' if not mr else 'सी.टी.एस. क्र.'}: {cts}")
    doc.gt("cts_number", cts.split()[-1], token=cts)
    doc.line(f"{'Owner' if not mr else 'मालक'}: {'Shri' if not mr else 'श्री'} {owner_name}")
    add_area(doc, rng, "sqm")
    doc.line(f"{'Date of Issue' if not mr else 'दिनांक'}: {date_text(issue_day, doc.lang)}")
    doc.line("The property card is maintained under the city survey rules."
             if not mr else "हे मालमत्ता पत्रक नगर सर्व्हे नियमांनुसार ठेवले जाते.")


def build_ec(doc: Doc, rng: random.Random) -> None:
    owner = name_pair(rng)
    village, district = pick(rng, VILLAGES), pick(rng, DISTRICTS)
    survey = pick(rng, SURVEYS)
    unit = "guntha" if doc.lang == "en" else "hectare"
    entry_day = date(rng.randint(2015, 2023), rng.randint(1, 12), rng.randint(1, 28))
    reg_no = f"MH-PUN-{entry_day.year}-{rng.randint(10000, 99999)}"
    referred_no = f"MH-PUN-{entry_day.year - 6}-{rng.randint(10000, 99999)}"
    mr = doc.lang == "mr"
    owner_name = owner[1] if mr else owner[0]

    doc.gt("owner_name", owner_name)
    doc.gt("survey_number", survey, token=survey)
    doc.gt("registration_number", reg_no, token=reg_no)
    doc.gt("registration_date", entry_day.isoformat(), token=date_text(entry_day, doc.lang))
    doc.notes.append("EC: registration number/date belong to the encumbrance (mortgage) entry.")

    title_row(doc, "Encumbrance Certificate", "भारनियमिता दाखला")
    doc.gt_row("village", "Village" if not mr else "गाव", village[1] if mr else village[0])
    doc.gt_row("district", "District" if not mr else "जिल्हा", district[1] if mr else district[0])
    doc.gt_row("survey_number", "Survey No." if not mr else "स.नं.", survey)
    doc.line(f"{'Owner' if not mr else 'मालक'}: {'Shri' if not mr else 'श्री'} {owner_name}")
    add_area(doc, rng, unit)
    doc.line("Encumbrance 1: Mortgage in favour of Pune Urban Co-operative Bank"
             if not mr else "भार १: पुणे अर्बन सहकारी बँकेच्या नावे बंधक")
    doc.line(f"{'Registration No.' if not mr else 'नोंदणी क्रमांक'}: {reg_no}")
    doc.gt("registration_number", reg_no, token=reg_no)
    entry_printed = date_text(entry_day, doc.lang)
    doc.line(f"{'Registration Date' if not mr else 'नोंदणी दिनांक'}: {entry_printed}")
    doc.gt("registration_date", entry_day.isoformat(), token=entry_printed)
    doc.gt_row("referred_document", "Referred Document" if not mr else "संदर्भित दस्तऐवज",
               f"Sale Deed No. {referred_no}" if not mr else f"खरेदीखत क्र. {referred_no}")
    doc.line("Certified that no other encumbrance was registered during the search period."
             if not mr else "शोध कालावधीत अन्य कोणताही भार नोंदणी झालेला नाही.")


BUILDERS = {
    "sale_deed": build_sale_deed,
    "agreement_to_sale": build_agreement_to_sale,
    "gift_deed": build_gift_deed,
    "7_12_extract": build_7_12_extract,
    "8a_record": build_8a_record,
    "ferfar": build_ferfar,
    "property_card": build_property_card,
    "ec": build_ec,
}


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def render_digital(pages: list[list[str]]) -> bytes:
    """Text-layer PDF: exact extraction, unshaped Devanagari (see module docstring)."""
    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page(width=A4_W, height=A4_H)
        y = MARGIN + LINE_H
        for line in lines:
            page.insert_text((MARGIN, y), line, fontsize=11, fontname="mh",
                             fontfile=str(FONT_FILE))
            y += LINE_H
    return doc.tobytes(deflate=True)


def render_shaped(page_lines: list[str]) -> pymupdf.Pixmap:
    """HTML-shaped page raster (correct Devanagari glyphs) as a Pixmap."""
    doc = pymupdf.open()
    page = doc.new_page(width=A4_W, height=A4_H)
    css = (f"@font-face {{ font-family: mh; src: url({FONT_URL}) }}\n"
           "* { font-family: mh; font-size: 11pt; }\n"
           "p { margin: 0 0 5px 0; }")
    body = "".join(f"<p>{html.escape(line)}</p>" for line in page_lines)
    page.insert_htmlbox(pymupdf.Rect(MARGIN, MARGIN, A4_W - MARGIN, A4_H - MARGIN), body, css=css)
    return page.get_pixmap(dpi=SCAN_DPI)


def degrade(pix: pymupdf.Pixmap, rng: random.Random) -> bytes:
    """Rotate + noise + JPEG round-trip; returns JPEG bytes."""
    arr = cv2.imdecode(np.frombuffer(pix.tobytes("png"), np.uint8), cv2.IMREAD_GRAYSCALE)
    height, width = arr.shape
    angle = rng.uniform(0.4, 2.0) * rng.choice((-1.0, 1.0))
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    rotated = cv2.warpAffine(arr, matrix, (width, height), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)
    noise = np.random.default_rng(rng.randrange(2**32)).normal(0, 6.0, rotated.shape)
    noisy = np.clip(rotated.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    ok, buffer = cv2.imencode(".jpg", noisy, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
    if not ok:  # pragma: no cover - encoder failure is environmental
        raise RuntimeError("JPEG encoding failed")
    return buffer.tobytes()


def render_scanned_pdf(pages: list[list[str]], rng: random.Random) -> bytes:
    doc = pymupdf.open()
    for lines in pages:
        jpeg = degrade(render_shaped(lines), rng)
        page = doc.new_page(width=A4_W, height=A4_H)
        page.insert_image(pymupdf.Rect(0, 0, A4_W, A4_H), stream=jpeg)
    return doc.tobytes(deflate=True)


def render_image(pages: list[list[str]], rng: random.Random, ext: str) -> bytes:
    jpeg = degrade(render_shaped(pages[0]), rng)
    if ext == "jpg":
        return jpeg
    image = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_GRAYSCALE)
    ok, buffer = cv2.imencode(".png", image)
    if not ok:  # pragma: no cover
        raise RuntimeError("PNG encoding failed")
    return buffer.tobytes()


# --------------------------------------------------------------------------
# Corpus composition
# --------------------------------------------------------------------------


def core_variant(index: int, lang: str) -> str:
    """Balanced mix: English and Marathi never confounded with variants."""
    scanned = (index % 2 == 0) if lang == "en" else (index % 2 == 1)
    return "scanned" if scanned else "digital"


def composition(seed: int) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for index, doc_type in enumerate(DOC_TYPE_ORDER):
        for lang_index, lang in enumerate(LANGS, start=1):
            rows.append((doc_type, lang, core_variant(index, lang), "pdf"))
    rows.append(("ferfar", "mr", "scanned", "jpg"))
    rows.append(("property_card", "en", "scanned", "png"))
    return rows


def build_document(doc_type: str, lang: str, variant: str, ext: str, number: int,
                   seed: int) -> Doc:
    filename = f"{doc_type}_{number:02d}_{lang}_{variant}.{ext}"
    doc = Doc(doc_type, lang, variant, filename)
    BUILDERS[doc_type](doc, random.Random(f"{seed}:{filename}"))
    if not doc.pages[0]:
        raise RuntimeError(f"{filename}: builder produced no lines")
    return doc


def write_fixture(doc: Doc, out_dir: Path, rng: random.Random) -> dict:
    if doc.variant == "digital":
        payload = render_digital(doc.pages)
    elif doc.filename.endswith(".pdf"):
        payload = render_scanned_pdf(doc.pages, rng)
    else:
        payload = render_image(doc.pages, rng, doc.filename.rsplit(".", 1)[-1])
    (out_dir / doc.filename).write_bytes(payload)

    ground_truth = {
        "filename": doc.filename,
        "doc_type": doc.doc_type,
        "language": "english" if doc.lang == "en" else "marathi",
        "variant": doc.variant,
        "expected": doc.expected,
        "tokens": doc.tokens,
        "notes": doc.notes,
    }
    (out_dir / (Path(doc.filename).stem + ".json")).write_text(
        json.dumps(ground_truth, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return ground_truth


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(Path.home() / "AppData/Local/Temp/propchain_fixtures"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--verify", action="store_true",
                        help="re-open every written fixture and check its page count/text layer")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    index_rng = random.Random(f"layout:{args.seed}")
    manifest: list[dict] = []
    rows = composition(args.seed)
    for number, (doc_type, lang, variant, ext) in enumerate(rows, start=1):
        doc = build_document(doc_type, lang, variant, ext, number, args.seed)
        ground_truth = write_fixture(doc, out_dir, index_rng)
        manifest.append(ground_truth)
        fields = ",".join(sorted(ground_truth["expected"]))
        print(f"  {doc.filename:40} {doc_type:18} {lang} {variant:8} fields={fields}")

    (out_dir / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n{len(manifest)} fixtures + ground truth written to {out_dir}")

    if args.verify:
        failures = 0
        for entry in manifest:
            path = out_dir / entry["filename"]
            pdf = pymupdf.open(path)
            pages = pdf.page_count
            text = "".join(pdf[i].get_text() for i in range(pages))
            pdf.close()
            ok = pages >= 1
            if entry["variant"] == "digital":
                ok = ok and len(text.strip()) >= 40
            print(f"  verify {entry['filename']:40} pages={pages} text_chars={len(text.strip())}"
                  f" {'OK' if ok else 'FAIL'}")
            failures += 0 if ok else 1
        if failures:
            print(f"VERIFY FAILED for {failures} fixture(s)")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
