"""Unit tests for ``app.services.classifier_keyword.KeywordDocClassifier``.

Standalone by design: no conftest fixtures, no app boot, no DB — only the
classifier plus the two contracts it must honour (``KNOWN_DOC_TYPES`` and the
``DocClassifier`` protocol).

The snippets are realistic one-to-two-line samples of what Maharashtra land
documents say (English and Marathi). Expectations are *determinate* ones:
either a distinctive phrase names the type outright, or one type clearly
out-scores a cross-reference to another (see ``test_precedence_*``).
"""

from __future__ import annotations

import pytest

from app.models.enums import KNOWN_DOC_TYPES
from app.services.classifier_keyword import ENGINE_VERSION, KeywordDocClassifier
from app.services.interfaces import ClassificationResult, DocClassifier

#: File name that carries no classification signal of its own.
SCAN = "scan_001.pdf"

#: (doc_type, text) — filename is SCAN, so only the OCR text can decide.
ENGLISH_SAMPLES: tuple[tuple[str, str], ...] = (
    (
        "sale_deed",
        "SALE DEED - vendor Suresh Deshmukh sold to vendee Rajesh Patil for a consideration "
        "of Rs 25,00,000; stamp duty paid before the sub-registrar.",
    ),
    (
        "agreement_to_sale",
        "AGREEMENT TO SALE - the vendor agrees to sell the flat to the purchaser; earnest "
        "money paid, balance at registration.",
    ),
    (
        "gift_deed",
        "GIFT DEED - the donor transfers the flat by way of gift to the donee; no money "
        "changed hands.",
    ),
    (
        "mortgage_deed",
        "MORTGAGE DEED - mortgagor Suresh Deshmukh mortgages the property to the mortgagee "
        "bank as security for the loan.",
    ),
    (
        "lease_deed",
        "LEASE DEED - the lessor lets the premises to the lessee for 11 months at a monthly "
        "rent of Rs 25,000.",
    ),
    (
        "partition_deed",
        "PARTITION DEED - the coparceners partition the joint family property; each sharer "
        "gets a separate share.",
    ),
    (
        "will",
        "LAST WILL AND TESTAMENT - the testator bequeaths the property to his son and appoints "
        "an executor.",
    ),
    (
        "7_12_extract",
        "7 / 12 Extract - Survey No. 124/A, Village Wagholi, Taluka Haveli, District Pune "
        "(Pik Pratyakshik).",
    ),
    (
        "8a_record",
        "VILLAGE FORM 8A - Record of Rights, Survey No. 124/A, Village Wagholi, District Pune.",
    ),
    (
        "ferfar",
        "FERFAR - Mutation Entry No. 456 recorded on the strength of the registered sale deed; "
        "Survey No. 124/A, Village Wagholi.",
    ),
    (
        "property_card",
        "PROPERTY CARD - City Survey No. 1234, CTS No. 567, issued by the City Survey Office, "
        "Mumbai.",
    ),
    (
        "ec",
        "ENCUMBRANCE CERTIFICATE - E.C. No. 123/2019, Sub-Registrar Office Pune; the land is "
        "free from encumbrance for 30 years.",
    ),
    (
        "rera",
        "RERA REGISTRATION - MahaRERA Registration No. P52100012345; project registered under "
        "the Real Estate Regulatory Authority.",
    ),
    (
        "court_document",
        "IN THE COURT OF THE CIVIL JUDGE, PUNE - Civil Suit No. 245/2019; decree passed in "
        "favour of the plaintiff.",
    ),
)

#: (doc_type, text) — Marathi samples (Marathi OCR text, filename carries nothing).
MARATHI_SAMPLES: tuple[tuple[str, str], ...] = (
    (
        "sale_deed",
        "विक्रीखत: विक्रेता सुरेश देशमुख, खरेदीदार राजेश पाटील, मोबदला रु. २५,००,०००, "
        "नोंदणी कार्यालय पुणे.",
    ),
    (
        "agreement_to_sale",
        "सामंजस्य करार: विक्री करारानुसार विक्रेता सुरेश देशमुख यांनी खरेदीदार राजेश पाटील यांना "
        "मालमत्ता विकण्याचे ठरविले; बयाणा रु. ५,००,०००.",
    ),
    (
        "gift_deed",
        "देणगी खत - देणगीदार सुरेश देशमुख यांनी बक्षीस देऊन मालमत्ता राजेश पाटील यांच्याकडे "
        "हस्तांतरित केली.",
    ),
    (
        "mortgage_deed",
        "गहाणखत - मालमत्ता पुणे जिल्हा सहकारी बँकेकडे तारण म्हणून गहाण ठेवण्यात आली.",
    ),
    (
        "lease_deed",
        "भाडेपट्टा - मालक सुरेश देशमुख यांनी भाडेकरू राजेश पाटील यांना दुकान भाड्याने दिले; "
        "मासिक भाडे रु. १५,०००.",
    ),
    (
        "partition_deed",
        "वाटणीपत्र - सुरेश व राजेश यांनी संयुक्त मालमत्तेची फाळणी करून वाटप केले; प्रत्येकाचा "
        "हिस्सा निश्चित केला.",
    ),
    (
        "will",
        "इच्छापत्र (मृत्युपत्र) - मयत श्री. सुरेश देशमुख यांनी मालमत्ता मुलगा राजेश याला "
        "दिलेली आहे.",
    ),
    (
        "7_12_extract",
        "गाव नमुना सात (सातबारा): गट नं. ४५६, धारणा खाते क्रमांक १२४, एकूण क्षेत्र १.२० हे.आर.",
    ),
    (
        "8a_record",
        "नमुना आठ-अ: गाव वाघोली, सर्व्हे नं. १२४/अ, मालक सुरेश देशमुख.",
    ),
    (
        "ferfar",
        "फेरफार नोंद क्रमांक ४५६ - गाव वाघोली, सर्व्हे नं. १२४/अ. फेरफार अभिलेखात मालकी हक्क बदल.",
    ),
    (
        "property_card",
        "मालमत्ता पत्रक - सिटी सर्व्हे क्रमांक १२३४, मालमत्ता कार्ड, नगरपालिका कार्यालय, पुणे.",
    ),
    (
        "ec",
        "भारनियमिता प्रमाणपत्र - गट नं. ४५६, खरेदी-विक्री भार, नोंदणी कार्यालय, पुणे. "
        "मालमत्तेवर कोणताही भार नाही.",
    ),
    (
        "rera",
        "महारेरा नोंदणी क्रमांक P52100012345 - रेरा प्रकल्प नोंदणी प्रमाणपत्र.",
    ),
    (
        "court_document",
        "न्यायालय, जिल्हा न्यायाधीश, पुणे - दावा क्रमांक २४५/२०१९. आदेश: वादीच्या बाजूने फैसला.",
    ),
)

ALL_SAMPLES = tuple(
    (language, doc_type, text)
    for language, samples in (("english", ENGLISH_SAMPLES), ("marathi", MARATHI_SAMPLES))
    for doc_type, text in samples
)

#: Filename-only inputs (text is None) that must still classify.
FILENAME_ONLY_CASES: tuple[tuple[str, str], ...] = (
    ("7_12_extract", "7_12_extract_demo.pdf"),
    ("7_12_extract", "712.pdf"),  # survey-number form, protected by the score floor
    ("gift_deed", r"C:\uploads\2019\gift_deed.pdf"),
    ("gift_deed", "GIFT-DEED-SCAN.PDF"),
    ("sale_deed", "sale_deed_final.pdf"),
    ("property_card", "property_card_cts.pdf"),
    ("ec", "ec_document.pdf"),
    ("ferfar", "mutation_extract.pdf"),
)

#: Inputs that must abstain.
UNKNOWN_CASES: tuple[tuple[str, str | None], ...] = (
    (SCAN, None),
    ("IMG_20240112_0045.jpg", None),
    (SCAN, ""),
    (SCAN, "   \n\t "),
    ("", None),
    (SCAN, "This is a scanned document about a property in Pune."),  # no signal
    (SCAN, "मालमत्ता आणि सर्व कागदपत्रे जोडली आहेत."),  # weak "मालमत्ता" only
    (SCAN, "वाटप गहाण"),  # weak signals, below the floor
)

#: Distinctive multi-signal English sale deed used by several tests.
STRONG_SALE_TEXT = (
    "SALE DEED - vendor Suresh Deshmukh sold to vendee Rajesh Patil for a consideration of "
    "Rs 25,00,000; stamp duty paid before the sub-registrar."
)


@pytest.fixture()
def clf() -> KeywordDocClassifier:
    return KeywordDocClassifier()


@pytest.mark.parametrize(
    "language,expected,text",
    ALL_SAMPLES,
    ids=[f"{language}-{doc_type}" for language, doc_type, _ in ALL_SAMPLES],
)
def test_english_and_marathi_snippet_classifies(clf, language, expected, text):
    result = clf.classify(SCAN, text)
    assert result.doc_type == expected, f"{language} sample misclassified: {result} / {text!r}"
    assert 0.0 < result.confidence <= 0.95


@pytest.mark.parametrize(
    "expected,filename",
    FILENAME_ONLY_CASES,
    ids=[filename for _, filename in FILENAME_ONLY_CASES],
)
def test_filename_only_fallback(clf, expected, filename):
    result = clf.classify(filename, None)
    assert result.doc_type == expected, f"{filename}: {result}"
    assert result.confidence >= 0.6  # a distinctive name alone is already good evidence


def test_text_only_classifies_with_uninformative_filename(clf):
    """The Marathi signal must win even when the file name says nothing at all."""
    text = "गहाणखत - मालमत्ता पुणे जिल्हा सहकारी बँकेकडे तारण म्हणून गहाण ठेवण्यात आली."
    result = clf.classify("IMG_20240112_0045.jpg", text)
    assert result.doc_type == "mortgage_deed"
    assert result.confidence >= 0.6


def test_page_separator_text_from_the_pipeline_is_classified(clf):
    """OCR text may join pages with form feeds (see interfaces.NLPExtractor)."""
    text = "SCANNED COPY\fSALE DEED - vendor Ramesh Patil, vendee Sunil Patil, stamp duty paid."
    assert clf.classify(SCAN, text).doc_type == "sale_deed"


@pytest.mark.parametrize(
    "filename,text",
    UNKNOWN_CASES,
    ids=[f"{filename!r}-{str(text)[:24]!r}" for filename, text in UNKNOWN_CASES],
)
def test_ambiguous_or_empty_input_is_unknown(clf, filename, text):
    result = clf.classify(filename, text)
    assert result.doc_type == "unknown", f"{filename!r} / {text!r} -> {result}"
    assert result.confidence <= 0.3


def test_weak_single_signal_stays_unknown(clf):
    """"stamp duty" (W_WEAK) is real evidence but not enough to name a type."""
    result = clf.classify(SCAN, "Payment of stamp duty receipt attached for reference.")
    assert result.doc_type == "unknown"
    assert result.confidence <= 0.3


def test_none_and_empty_text_behave_the_same(clf):
    assert clf.classify(SCAN, None) == clf.classify(SCAN, "")
    assert clf.classify(SCAN, None).doc_type == "unknown"


def test_classification_is_case_insensitive(clf):
    lower = clf.classify(SCAN, STRONG_SALE_TEXT.lower())
    upper = clf.classify(SCAN, STRONG_SALE_TEXT.upper())
    mixed = clf.classify(SCAN, "Gift Deed - the Donor gives by way of Gift to the Donee.")
    assert lower.doc_type == upper.doc_type == "sale_deed"
    assert lower.confidence == upper.confidence
    assert mixed.doc_type == "gift_deed"


def test_single_distinctive_signal_is_at_least_sixty_percent(clf):
    """One unambiguous phrase ("सातबारा", "इच्छापत्र") must be >= 0.60."""
    for text, expected in (
        ("सातबारा", "7_12_extract"),
        ("इच्छापत्र", "will"),
        ("encumbrance", "ec"),
    ):
        result = clf.classify(SCAN, text)
        assert result.doc_type == expected, (text, result)
        assert result.confidence >= 0.6, (text, result)


def test_strong_multi_signal_evidence_is_at_least_eighty_percent(clf):
    """Filename and text agreeing on several signals must be >= 0.80."""
    result = clf.classify("sale_deed_2019.pdf", STRONG_SALE_TEXT)
    assert result.doc_type == "sale_deed"
    assert result.confidence >= 0.8


def test_channels_are_additive(clf):
    """The same phrase in the text, the name, and both: confidence must increase.

    The file name is worth 2x per signal (FILENAME_WEIGHT), so one name hit
    (6.0) already beats one text hit (3.0), and both together (9.0) beat either.
    """
    text_only = clf.classify(SCAN, "sale deed")
    name_only = clf.classify("sale_deed.pdf", None)
    both = clf.classify("sale_deed.pdf", "sale deed")
    assert text_only.doc_type == name_only.doc_type == both.doc_type == "sale_deed"
    assert text_only.confidence < name_only.confidence < both.confidence


def test_confidence_is_clamped_to_the_documented_maximum(clf):
    """Even overwhelming evidence never claims more than MAX_CONFIDENCE (0.95)."""
    both = clf.classify(
        "sale_deed_registered_vendor_vendee.pdf",
        STRONG_SALE_TEXT + " सोबत सातबारा उतारा जोडलेला आहे.",
    )
    assert both.doc_type == "sale_deed"
    assert 0.8 <= both.confidence <= 0.95


def test_precedence_7_12_extract_with_village_mention(clf):
    """A 7/12 extract that names the village (गाव) stays a 7/12 extract.

    "गाव" (village) is deliberately not a signal of any type; only the
    7/12 phrases decide this document.
    """
    for text in (
        "सातबारा - गाव वाघोली, ता. हवेली, जि. पुणे. गट नं. ४५६, क्षेत्र १.२० हे.आर.",
        "गाव नमुना सात: गाव वाघोली, सर्व्हे नं. १२४/अ, एकूण क्षेत्र २ हे.आर.",
    ):
        assert clf.classify(SCAN, text).doc_type == "7_12_extract", text


def test_precedence_sale_deed_referencing_a_7_12_extract(clf):
    """A sale deed that merely *attaches* a 7/12 stays a sale deed.

    The sale signals (विक्रीखत + विक्रेता + खरेदीदार + मोबदला) out-score the
    single reference to the attached 7/12 extract, and they keep out-scoring it
    when the reference is spelled "7/12" as well as "सातबारा".
    """
    body = (
        "विक्रीखत - विक्रेता सुरेश देशमुख, खरेदीदार राजेश पाटील, मोबदला रु. २५,००,०००. "
    )
    attached_only = clf.classify(SCAN, body + "सोबत सातबारा उतारा जोडलेला आहे.")
    attached_numbered = clf.classify(SCAN, body + "सोबत सातबारा (7/12) उतारा जोडलेला आहे.")
    assert attached_only.doc_type == "sale_deed", attached_only
    assert attached_numbered.doc_type == "sale_deed", attached_numbered


def test_precedence_text_evidence_can_outweigh_a_filename(clf):
    """Evidence is additive: strong Marathi text wins over a weak name hint.

    "mutation_note.pdf" hints at a ferfar (one weak signal, x2 = 3.0), while the
    text carries two mortgage signals (गहाणखत + तारण + गहाण), so the text wins.
    """
    result = clf.classify("mutation_note.pdf", "गहाणखत - मालमत्ता बँकेकडे तारण म्हणून गहाण ठेवली.")
    assert result.doc_type == "mortgage_deed", result


def test_tie_is_deterministic_and_low_confidence(clf):
    """A genuine tie is broken deterministically (score, breadth, machine value).

    "पट्टा" (lease) and "तारण" (mortgage) are both exactly W_STRONG, so the
    documented final tie-break (ascending doc_type) picks lease_deed — and the
    dominance discount keeps the confidence visibly low.
    """
    first = clf.classify(SCAN, "पट्टा तारण")
    second = clf.classify(SCAN, "पट्टा तारण")
    assert first == second
    assert first.doc_type == "lease_deed", first
    assert first.confidence < 0.6


def test_engine_version_is_reported(clf):
    assert KeywordDocClassifier.engine_version == ENGINE_VERSION == "keyword-v1"
    result = clf.classify("sale_deed.pdf", STRONG_SALE_TEXT)
    assert result.engine_version == ENGINE_VERSION
    assert isinstance(result, ClassificationResult)


def test_satisfies_doc_classifier_protocol(clf):
    assert isinstance(clf, DocClassifier)
    assert isinstance(clf.engine_version, str)


def test_every_emitted_doc_type_is_a_known_machine_value(clf):
    """Guard: only KNOWN_DOC_TYPES values, and never the reviewer-owned "other"."""
    inputs: list[tuple[str, str | None]] = [(SCAN, text) for _, _, text in ALL_SAMPLES]
    inputs += [(filename, None) for _, filename in FILENAME_ONLY_CASES]
    inputs += list(UNKNOWN_CASES)
    inputs += [
        (SCAN, "पट्टा तारण"),
        (SCAN, "encumbrance"),
        (SCAN, "गहाणखत"),
        (SCAN, "This is a scanned document about a property in Pune."),
        ("sale_deed_2019.pdf", STRONG_SALE_TEXT),
    ]
    for filename, text in inputs:
        result = clf.classify(filename, text)
        assert result.doc_type in KNOWN_DOC_TYPES, (filename, text, result)
        assert result.doc_type != "other", ("other is reserved for reviewers", filename, text)
        assert 0.0 <= result.confidence <= 0.95, (filename, text, result)
        assert result.engine_version == "keyword-v1"
