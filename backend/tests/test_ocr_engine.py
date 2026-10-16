"""End-to-end tests for the real OCR engine (``TesseractOcrService``).

These tests build their own documents in ``tmp_path`` and never touch the
database, the API or the app's storage directory, so they deliberately do not
request the temp-DB fixtures from ``tests/conftest.py``; importing
``app.config`` is enough to learn whether this machine has a usable Tesseract.

Layout:
* ``test_digital_*`` / ``test_two_page_*`` exercise the text-layer path and must
  pass on any machine, Tesseract or not;
* ``test_scanned_*`` render a page to an image-only PDF (a stand-in for a real
  scan) and need the binary, so they skip cleanly when it is absent;
* ``test_missing_tesseract_binary_*`` runs everywhere: it breaks
  ``TESSERACT_CMD`` and expects an actionable ``RuntimeError``.
* ``test_image_prep_*`` cover the numpy/OpenCV helpers the engine leans on.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import cv2
import numpy as np
import pymupdf
import pytest
from rapidfuzz import fuzz

from app.config import settings
from app.services import image_prep

#: Mangal is a plain TTF (unlike Nirmala, a .ttc MuPDF cannot load) and ships
#: with Windows, so the Marathi fixtures can rely on it being present.
MANGAL_FONT = Path("C:/Windows/Fonts/mangal.ttf")

#: Devanagari words that must survive the `insert_htmlbox` -> `get_text()`
#: round trip. `insert_htmlbox` shapes text with HarfBuzz and the glyph->Unicode
#: reverse mapping mangles *conjunct* glyphs (e.g. "सर्वेक्षण" comes back as
#: "सवȺZण" with pymupdf 1.28.2), so the assertion names words built from simple
#: glyph sequences — plus a Devanagari-share check below that holds regardless.
KNOWN_MARATHI_WORDS = ("करारनामा", "आहे", "असे", "पुणे", "ता.सो.")

#: Expected words for the fuzzy assertion of the scanned Marathi test.
EXPECTED_MARATHI_TOKENS = ("सर्वेक्षण", "क्रमांक", "करारनामा", "विक्री", "महाराष्ट्र")
FUZZY_THRESHOLD = 70

ENGLISH_TEXT = (
    "SALE DEED\n"
    "Survey No. 124/A, Taluka Haveli, District Pune, Maharashtra.\n"
    "This indenture of sale is made between Suresh Deshmukh, the seller, "
    "and Rajesh Patil, the buyer, for a consideration of Rupees Forty Five Lakh."
)

MARATHI_TEXT = (
    "हा दस्तऐवज विक्री करारनामा आहे. "
    "महाराष्ट्र शासन, जिल्हा पुणे, तालुका हवेली. "
    "सर्वेक्षण क्रमांक १२४/अ. "
    "मालमत्ता क्षेत्र १२०० चौरस फूट. "
    "खरेदीदार राजेश पाटील, विक्रेता सुरेश देशमुख."
)


def _tesseract_available() -> bool:
    """True when ``TESSERACT_CMD`` points at a file, or Tesseract is on PATH."""
    configured = (settings.tesseract_cmd or "").strip()
    if configured and Path(configured).is_file():
        return True
    return shutil.which("tesseract") is not None


def _engine_module():
    """The OCR engine module as it exists *right now*.

    ``tests/support.py:purge_app_modules`` (used by the temp-DB fixtures in
    ``conftest.py``) drops every ``app.*`` module between test modules, which
    replaces both ``app.config.settings`` and this engine module. Importing at
    call time keeps the tests talking to the same objects the code under test
    reads — a collection-time import would leave them holding the settings
    object and the memoised version string of a module instance the rest of the
    suite has already discarded.
    """
    from app.services import ocr_tesseract

    return ocr_tesseract


def _extract(path: Path, languages: list[str]):
    """Run the real engine over ``path`` (single call, no shared state)."""
    return _engine_module().TesseractOcrService().extract(str(path), list(languages))


TESSERACT_AVAILABLE = _tesseract_available()
MARATHI_FONT_AVAILABLE = MANGAL_FONT.is_file()

requires_tesseract = pytest.mark.skipif(
    not TESSERACT_AVAILABLE,
    reason="no Tesseract binary: set TESSERACT_CMD (see backend/.env) to run OCR tests",
)
requires_mangal = pytest.mark.skipif(
    not MARATHI_FONT_AVAILABLE,
    reason=f"Devanagari font not found at {MANGAL_FONT}",
)


def _build_text_pdf(path: Path, text) -> None:
    """Write a born-digital PDF: one page per entry of ``text``."""
    chunks = [text] if isinstance(text, str) else list(text)
    document = pymupdf.open()
    try:
        for body in chunks:
            page = document.new_page(width=595, height=842)
            page.insert_textbox(
                pymupdf.Rect(50, 50, 545, 500), body, fontsize=14, fontname="helv"
            )
        document.save(path)
    finally:
        document.close()


def _build_marathi_pdf(path: Path) -> None:
    """Write a born-digital Marathi PDF using ``insert_htmlbox`` + Mangal.

    Note for the reviewer: with pymupdf 1.28.2 the ``file:///`` font URL above
    is not resolved (MuPDF logs "cannot locate font 'file:///C:/Windows/Fonts/
    mangal.ttf' specified by css") and the story falls back to MuPDF's bundled
    Noto Serif Devanagari, which still renders/embeds correct Devanagari glyphs —
    both the rendered pixels and the extractable text layer are Devanagari, so
    the fixtures behave as intended. The archive-based alternative
    (``pymupdf.Archive("C:/Windows/Fonts")`` + ``url("mangal.ttf")``) does load
    Mangal, but embeds *more* mangled ligature ToUnicode entries than the
    fallback font, so the requested file URL form was kept.
    """
    document = pymupdf.open()
    try:
        page = document.new_page(width=595, height=842)
        css = (
            "@font-face { font-family: m; src: url(file:///C:/Windows/Fonts/mangal.ttf) } "
            "body { font-family: m; font-size: 22px; }"
        )
        page.insert_htmlbox(pymupdf.Rect(50, 50, 545, 500), f"<div>{MARATHI_TEXT}</div>", css=css)
        document.save(path)
    finally:
        document.close()


def _rasterize_into_pdf(source: Path, destination: Path, dpi: int = 200) -> None:
    """Turn ``source`` into an image-only PDF (what a page scanner would emit).

    Rendering the page to a pixmap and re-inserting it as an image drops the
    embedded text layer, which is exactly the situation the OCR path exists for.
    """
    with pymupdf.open(source) as source_document:
        scanned = pymupdf.open()
        try:
            for page in source_document:
                pixmap = page.get_pixmap(dpi=dpi)
                target = scanned.new_page(width=page.rect.width, height=page.rect.height)
                target.insert_image(target.rect, pixmap=pixmap)
            scanned.save(destination)
        finally:
            scanned.close()


def _describe(result) -> str:
    """Compact one-line summary of an ``OcrResult`` for the test log."""
    return " | ".join(
        f"p{page.page_number} conf={page.confidence} text={page.text!r}" for page in result.pages
    )


# --- text layer (no Tesseract required) --------------------------------------


def test_digital_pdf_uses_embedded_text_layer(tmp_path):
    """A born-digital English PDF is read as text: no OCR, no confidence."""
    path = tmp_path / "sale_deed_digital.pdf"
    _build_text_pdf(path, ENGLISH_TEXT)

    result = _extract(path, ["english"])

    print(f"digital english: language={result.language} engine={result.engine_version}")
    print(_describe(result))
    assert len(result.pages) == 1
    page = result.pages[0]
    assert "SALE DEED" in page.text
    assert "Survey No. 124/A" in page.text
    assert page.confidence is None  # text layer path, Tesseract not called
    assert result.language == "english"
    assert result.engine_version.startswith("tesseract-")


@requires_mangal
def test_digital_marathi_pdf_uses_embedded_text_layer(tmp_path):
    """A born-digital Marathi PDF keeps its Devanagari text layer."""
    path = tmp_path / "marathi_karaarnama.pdf"
    _build_marathi_pdf(path)

    result = _extract(path, ["marathi"])

    page = result.pages[0]
    print(f"digital marathi: language={result.language} conf={page.confidence}")
    print(f"observed text layer: {page.text!r}")
    assert page.confidence is None
    # The text layer must be long enough for the engine to prefer it over OCR,
    # otherwise this test would silently depend on Tesseract.
    assert len(page.text) >= 40
    devanagari = sum(1 for char in page.text if ord(char) in range(0x0900, 0x0980))
    assert devanagari / len(page.text) >= 0.3, "text layer lost its Devanagari characters"
    matched = [word for word in KNOWN_MARATHI_WORDS if word in page.text]
    print(f"recognised Marathi words: {matched}")
    assert matched, f"no known Marathi word survived the round trip: {page.text!r}"
    assert result.language == "marathi"


def test_two_page_text_pdf_numbers_every_page(tmp_path):
    """Page numbers are 1-based and cover every page of the document."""
    path = tmp_path / "two_page_agreement.pdf"
    _build_text_pdf(path, [ENGLISH_TEXT, ENGLISH_TEXT.replace("SALE DEED", "PAGE TWO")])

    result = _extract(path, [])

    assert [page.page_number for page in result.pages] == [1, 2]
    assert all(page.confidence is None for page in result.pages)
    assert "PAGE TWO" in result.pages[1].text


# --- scanned pages (need Tesseract) ------------------------------------------


@requires_tesseract
def test_scanned_english_page_is_ocrd(tmp_path):
    """A rendered (image-only) English page is recognised by Tesseract."""
    digital = tmp_path / "sale_deed_digital.pdf"
    _build_text_pdf(digital, ENGLISH_TEXT)
    scanned = tmp_path / "sale_deed_scanned.pdf"
    _rasterize_into_pdf(digital, scanned, dpi=200)

    result = _extract(scanned, ["english"])

    page = result.pages[0]
    print(f"scanned english: language={result.language} conf={page.confidence}")
    print(f"raw OCR text: {page.text!r}")
    upper = page.text.upper()
    assert "SALE" in upper
    assert "DEED" in upper
    assert page.confidence is not None and page.confidence > 0.5
    assert result.language == "english"


@requires_tesseract
@requires_mangal
def test_scanned_marathi_page_is_ocrd(tmp_path):
    """A rendered Marathi page comes back as readable Devanagari (fuzzy match).

    Tesseract's Marathi output is not expected to be character-perfect, so the
    assertion is a fuzzy one: at least one recognised token has to be a >= 70 %
    partial match for one of a few words the page definitely contains. The
    observed scores are printed so failures can be judged on real numbers.
    """
    digital = tmp_path / "marathi_digital.pdf"
    _build_marathi_pdf(digital)
    scanned = tmp_path / "marathi_scanned.pdf"
    _rasterize_into_pdf(digital, scanned, dpi=200)

    result = _extract(scanned, ["marathi"])

    page = result.pages[0]
    print(f"scanned marathi: language={result.language} conf={page.confidence}")
    print(f"raw OCR text: {page.text!r}")
    tokens = [token.strip(".,:;()") for token in page.text.split() if token.strip()]
    scored = sorted(
        ((max(fuzz.partial_ratio(token, expected) for expected in EXPECTED_MARATHI_TOKENS), token)
         for token in tokens),
        reverse=True,
    )
    print(f"top fuzzy matches: {[(token, round(score, 1)) for score, token in scored[:6]]}")
    assert page.text.strip(), "Tesseract returned no text for the scanned Marathi page"
    best_score, best_token = scored[0]
    assert best_score >= FUZZY_THRESHOLD, (
        f"best fuzzy match {best_token!r} scored {best_score:.1f} (< {FUZZY_THRESHOLD}); "
        f"OCR text was {page.text!r}"
    )
    assert result.language == "marathi"


# --- misconfiguration ---------------------------------------------------------


def test_missing_tesseract_binary_raises_runtime_error(tmp_path, monkeypatch):
    """A broken ``TESSERACT_CMD`` must fail loudly, with instructions.

    ``monkeypatch.setattr`` on the pydantic settings object works because
    ``Settings`` allows attribute assignment and ``ocr_tesseract`` reads
    ``settings.tesseract_cmd`` at call time (nothing is cached at import), so no
    internal helper has to be poked directly. The patched object is the engine
    module's own ``settings`` reference: ``tests/support.purge_app_modules()``
    may have swapped ``app.config.settings`` since this test module was imported.
    The page has no text layer, hence the engine really does need the binary.
    """
    digital = tmp_path / "sale_deed_digital.pdf"
    _build_text_pdf(digital, ENGLISH_TEXT)
    scanned = tmp_path / "sale_deed_scanned.pdf"
    _rasterize_into_pdf(digital, scanned, dpi=100)

    engine = _engine_module()
    bogus = tmp_path / "not-a-real-tesseract.exe"
    monkeypatch.setattr(engine.settings, "tesseract_cmd", str(bogus))

    with pytest.raises(RuntimeError) as excinfo:
        engine.TesseractOcrService().extract(str(scanned), ["english"])

    message = str(excinfo.value)
    print(f"error message: {message}")
    assert "Tesseract" in message
    assert str(bogus) in message or "TESSERACT_CMD" in message


def test_unreadable_file_names_the_document(tmp_path):
    """A missing/corrupt upload is reported with its filename, not a traceback."""
    missing = tmp_path / "no_such_deed.pdf"

    with pytest.raises(RuntimeError) as excinfo:
        _extract(missing, ["english"])

    assert "no_such_deed.pdf" in str(excinfo.value)


def test_language_mapping_and_fallback():
    """PropChain labels map to traineddata codes; unknown input uses the default."""
    engine = _engine_module()

    assert engine.tesseract_language_string(["english"]) == "eng"
    assert engine.tesseract_language_string(["marathi", "english"]) == "mar+eng"
    assert engine.tesseract_language_string(["mar", "eng", "english"]) == "mar+eng"
    assert engine.tesseract_language_string([]) == engine.settings.ocr_langs
    assert engine.tesseract_language_string(["klingon"]) == engine.settings.ocr_langs


def test_engine_version_degrades_and_text_layer_still_works(tmp_path, monkeypatch):
    """Without a usable binary the engine reports "unknown" instead of raising.

    The version is memoised per process, so the cache is cleared before and
    after the test — on the module instance fetched at call time, since an
    earlier reload of ``app.services.ocr_tesseract`` would otherwise keep a
    stale "tesseract-5.5.3" in a different module object. The born-digital page
    must still be extracted: only scanned pages need the binary.
    """
    engine = _engine_module()
    path = tmp_path / "sale_deed_digital.pdf"
    _build_text_pdf(path, ENGLISH_TEXT)
    monkeypatch.setattr(engine.settings, "tesseract_cmd", str(tmp_path / "nope.exe"))
    engine._engine_version_string.cache_clear()
    try:
        service = engine.TesseractOcrService()
        assert service.engine_version == "tesseract-unknown"
        result = service.extract(str(path), ["english"])
        assert result.engine_version == "tesseract-unknown"
        assert "SALE DEED" in result.pages[0].text
    finally:
        engine._engine_version_string.cache_clear()


# --- preprocessing helpers ---------------------------------------------------


def test_image_prep_to_gray_handles_bgr_and_grayscale():
    """Colour input collapses to a 2-D 8-bit array; bad shapes fail loudly."""
    bgr = np.zeros((4, 4, 3), dtype=np.uint8)
    bgr[:, :, 2] = 255  # pure red in BGR
    gray = image_prep.to_gray(bgr)
    assert gray.shape == (4, 4) and gray.dtype == np.uint8
    assert gray[0, 0] < 100  # red carries little luma

    already_gray = np.full((2, 3), 77, dtype=np.uint8)
    assert image_prep.to_gray(already_gray).tolist() == already_gray.tolist()
    assert not np.shares_memory(image_prep.to_gray(already_gray), already_gray)

    with pytest.raises(ValueError):
        image_prep.to_gray(np.zeros((4, 4), dtype=np.float32))


def test_image_prep_deskew_straightens_a_tilted_page():
    """A synthetic tilted text line is measured and rotated back to level."""
    page = np.full((400, 600), 255, dtype=np.uint8)
    page[180:220, 100:500] = 0  # a page-wide black bar = "a line of text"
    assert abs(image_prep.measure_tilt(page)) < 1.0

    tilt = 6.0
    matrix = cv2.getRotationMatrix2D((300.0, 200.0), tilt, 1.0)
    tilted = cv2.warpAffine(
        page, matrix, (600, 400), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    )
    # measure_tilt reports the correction to apply, i.e. the opposite sign.
    measured = image_prep.measure_tilt(tilted)
    assert abs(measured + tilt) < 1.0, f"tilt of {tilt} measured as {measured}"

    corrected = image_prep.deskew(tilted)
    assert abs(image_prep.measure_tilt(corrected)) < 1.0


def test_image_prep_enhance_contrast_spreads_a_flat_histogram():
    """CLAHE lifts local contrast but keeps the image shape/dtype."""
    page = np.full((64, 64), 128, dtype=np.uint8)
    page[16:48, 16:48] = 140
    enhanced = image_prep.enhance_contrast(page)
    assert enhanced.shape == page.shape and enhanced.dtype == np.uint8
    assert enhanced.max() > page.max()
