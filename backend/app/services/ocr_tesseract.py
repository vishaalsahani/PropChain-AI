"""Tesseract-backed implementation of the OCR engine interface.

Called through :func:`app.services.registry.get_ocr_service` when
``OCR_ENGINE=tesseract``; the class only needs :class:`OcrService`'s two
members (``engine_version`` and ``extract``).

Behaviour worth knowing
-----------------------
* A page that already carries a usable text layer (>= :data:`TEXT_LAYER_MIN_CHARS`
  characters) is returned verbatim with ``confidence=None`` and Tesseract is
  never invoked — a digitally generated deed must not be re-OCR'd, both for
  accuracy and for speed. That also means the engine works on a machine without
  Tesseract for born-digital uploads.
* Scanned pages are rasterized at ``settings.ocr_dpi`` (default 300 dpi),
  converted to a grayscale numpy array, preprocessed (deskew -> CLAHE, see
  :mod:`app.services.image_prep`) and handed to ``pytesseract.image_to_data``
  so per-word confidences survive. A page's confidence is the mean token
  confidence (tokens with ``conf >= 0``) scaled to 0..1.
* ``OcrResult.language`` is *observed* from the extracted text (Devanagari vs
  Latin letter counts), not echoed back from the request.
* Importing this module never touches the Tesseract binary. A missing binary is
  reported as ``RuntimeError`` (with TESSERACT_CMD instructions) on the first
  page that actually needs OCR, so a misconfigured machine still boots and still
  serves digital documents.
"""

from __future__ import annotations

import logging
import shutil
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pymupdf
import pytesseract
from pytesseract import Output, TesseractError, TesseractNotFoundError

from app.config import settings
from app.services import image_prep
from app.services.interfaces import OcrPage, OcrResult

logger = logging.getLogger(__name__)

#: PropChain language label -> Tesseract traineddata code.
LANGUAGE_ALIASES: dict[str, str] = {
    "marathi": "mar",
    "english": "eng",
    "mar": "mar",
    "eng": "eng",
}

#: Shortest embedded text layer that counts as "born digital" (characters).
TEXT_LAYER_MIN_CHARS = 40

#: Share of Devanagari letters above which a document counts as Marathi.
DEVANAGARI_RATIO_THRESHOLD = 0.30

#: Unicode block used for the Devanagari letter count (U+0900..U+097F).
DEVANAGARI_BLOCK = range(0x0900, 0x0980)

_TESSERACT_HINT = (
    "Install Tesseract and point TESSERACT_CMD at the executable "
    "(and TESSDATA_PREFIX at its tessdata directory) in backend/.env, or set "
    "OCR_ENGINE=fake to use the mock engine."
)


def tesseract_language_string(languages: list[str] | None) -> str:
    """Map PropChain language labels onto a Tesseract ``-l`` string.

    ``["english", "marathi"]`` -> ``"eng+mar"``. Unknown or empty input falls
    back to ``settings.ocr_langs`` (the deployment default, "eng+mar"), so a
    caller can safely pass the value it read off a document.
    """
    codes = [
        LANGUAGE_ALIASES[label.strip().lower()]
        for label in (languages or [])
        if label and label.strip().lower() in LANGUAGE_ALIASES
    ]
    if codes:
        # dict.fromkeys keeps the caller's order but drops duplicates.
        return "+".join(dict.fromkeys(codes))
    fallback = (settings.ocr_langs or "").strip()
    return fallback or "eng"


def detect_language(text: str) -> str | None:
    """Guess the document language from the characters that were extracted.

    Counts Devanagari characters (U+0900..U+097F, which includes the Devanagari
    digits) against Latin letters ``A-Z``/``a-z``. A Devanagari share of at
    least :data:`DEVANAGARI_RATIO_THRESHOLD` wins, because Marathi property
    documents routinely mix in English headings ("SALE DEED", "Survey No.") and
    a bare majority test would misclassify them as English.

    Returns ``"marathi"``, ``"english"``, or ``None`` when the text holds no
    letters at all (blank scan / numbers only).
    """
    devanagari = sum(1 for char in text if ord(char) in DEVANAGARI_BLOCK)
    latin = sum(1 for char in text if char.isascii() and char.isalpha())
    total = devanagari + latin
    if total == 0:
        return None
    if devanagari / total >= DEVANAGARI_RATIO_THRESHOLD:
        return "marathi"
    if latin:
        return "english"
    return None


def resolve_tesseract_cmd() -> str | None:
    """Absolute path of the Tesseract binary, or ``None`` when it is missing.

    ``settings.tesseract_cmd`` wins when set (this box has Tesseract in a
    conda-style ``tessenv`` and it is not on PATH); otherwise ``shutil.which``
    looks the executable up on PATH.
    """
    configured = (settings.tesseract_cmd or "").strip()
    if configured:
        return configured
    return shutil.which("tesseract")


def tesseract_config() -> str:
    """Extra Tesseract command line options for the current settings.

    ``--tessdata-dir`` is added when ``settings.tessdata_prefix`` is set.
    Quoting caveat: pytesseract splits this string with
    ``shlex.split(config, posix=not win32)``. On POSIX the quotes are stripped,
    so a quoted path is both correct and space-safe; on Windows the quotes
    survive the split and are passed to Tesseract literally (verified against
    pytesseract 0.3.13: ``Error opening data file "C:\\...\\tessdata"/mar.traineddata``),
    so the path is passed unquoted there — and omitted entirely when it contains
    whitespace, in which case :func:`_configure_tessdata_prefix` hands the
    directory over through the ``TESSDATA_PREFIX`` environment instead.
    """
    prefix = (settings.tessdata_prefix or "").strip()
    if not prefix:
        return ""
    if sys.platform == "win32":
        if " " in prefix or '"' in prefix:
            return ""
        return f"--tessdata-dir {prefix}"
    return f'--tessdata-dir "{prefix}"'


def _configure_tessdata_prefix() -> None:
    """Point Tesseract's child process at ``settings.tessdata_prefix``.

    pytesseract snapshots ``os.environ`` into its own module-level ``environ``
    dictionary at import time and passes that copy to every subprocess, so the
    copy is the only place where an environment override takes effect at
    runtime. Patching it (instead of ``os.environ``) keeps the change local to
    the OCR engine and works for paths containing spaces.
    """
    prefix = (settings.tessdata_prefix or "").strip()
    if prefix:
        pytesseract.pytesseract.environ["TESSDATA_PREFIX"] = prefix


def _ensure_tesseract_available() -> str:
    """Validate the configured binary and wire it into pytesseract.

    Raises ``RuntimeError`` (never ``TesseractNotFoundError``) when the binary
    is missing, because that is a deployment problem the pipeline should report
    as a failed analysis rather than crash on. A configured-but-broken
    ``TESSERACT_CMD`` is an error even if another Tesseract sits on PATH: silent
    fallbacks would hide the misconfiguration.
    """
    cmd = resolve_tesseract_cmd()
    if not cmd or not Path(cmd).is_file():
        raise RuntimeError(
            f"Tesseract binary not found (TESSERACT_CMD={cmd!r}). {_TESSERACT_HINT}"
        )
    pytesseract.pytesseract.tesseract_cmd = cmd
    _configure_tessdata_prefix()
    return cmd


@lru_cache(maxsize=1)
def _engine_version_string() -> str:
    """``"5.5.3"``-style Tesseract version, or ``"unknown"`` (never raises).

    Cached for the process lifetime: the version of a fixed binary cannot
    change, and ``extract`` reports it on every document. On failure the engine
    still reports ``tesseract-unknown`` instead of breaking the health of an
    otherwise working deployment. The cache can be dropped in tests with
    ``_engine_version_string.cache_clear()``.
    """
    cmd = resolve_tesseract_cmd()
    if cmd:
        # Assigned even when the path does not exist, so a broken TESSERACT_CMD
        # degrades to "unknown" instead of silently reporting whichever other
        # Tesseract pytesseract last happened to point at.
        pytesseract.pytesseract.tesseract_cmd = cmd
        _configure_tessdata_prefix()
    try:
        return str(pytesseract.get_tesseract_version())
    except (Exception, SystemExit) as exc:  # pytesseract raises SystemExit on a
        # version string it cannot parse (get_tesseract_version's parse() step).
        logger.warning("Could not determine the Tesseract version: %s", exc)
        return "unknown"


def _pixmap_to_bgr(pix: pymupdf.Pixmap) -> np.ndarray:
    """Convert a PyMuPDF pixmap into a numpy array (gray or BGR).

    ``pix.samples`` is a flat byte buffer whose rows are ``pix.stride`` bytes
    long, which is usually wider than ``width * n``; the padding has to be cut
    away before reshaping, otherwise the image shears diagonally. MuPDF's
    default page rasterization is RGB, so the colour channels are reversed into
    OpenCV's BGR order. A gray pixmap (``n == 1``) is passed through as 2-D.
    """
    buffer = np.frombuffer(pix.samples, dtype=np.uint8)
    rows = np.ascontiguousarray(buffer.reshape(pix.height, pix.stride)[:, : pix.width * pix.n])
    if pix.n == 1:
        return rows.reshape(pix.height, pix.width)
    if pix.n == 3:
        return np.ascontiguousarray(rows.reshape(pix.height, pix.width, 3)[:, :, ::-1])
    if pix.n == 4 and pix.alpha:
        # RGBA sample order -> BGR (background with no alpha support upstream).
        return np.ascontiguousarray(rows.reshape(pix.height, pix.width, 4)[:, :, [2, 1, 0]])
    # n == 4 without alpha is CMYK, which page.get_pixmap() only produces when a
    # caller explicitly asks for it; unsupported rather than silently misread.
    raise RuntimeError(
        f"Unsupported pixmap layout: n={pix.n}, alpha={getattr(pix, 'alpha', None)}"
    )


def _assemble_page_text(data: dict) -> tuple[str, float]:
    """Rebuild page text and mean confidence from ``image_to_data`` output.

    Tesseract's TSV/DICT output is a flat token list; consecutive tokens sharing
    the same ``(block_num, par_num, line_num)`` are one visual line, and a new
    tuple starts a new line. Empty tokens (layout-only rows) are skipped. The
    returned confidence is the mean of every token with ``conf >= 0`` (Tesseract
    uses -1 for rows it did not score) divided by 100 to land on the 0..1 scale
    the rest of the app uses; ``0.0`` when the page produced no scored token.
    """
    texts = data.get("text") or []
    confs = data.get("conf") or []
    blocks = data.get("block_num") or []
    paragraphs = data.get("par_num") or []
    lines = data.get("line_num") or []

    grouped: list[list[str]] = []
    current_key: tuple | None = None
    scores: list[float] = []

    for index, raw_token in enumerate(texts):
        token = (raw_token or "").strip()
        if not token:
            continue
        key = (
            blocks[index] if index < len(blocks) else None,
            paragraphs[index] if index < len(paragraphs) else None,
            lines[index] if index < len(lines) else None,
        )
        if key != current_key:
            grouped.append([])
            current_key = key
        grouped[-1].append(token)
        try:
            confidence = float(confs[index])
        except (IndexError, TypeError, ValueError):
            confidence = -1.0
        if confidence >= 0:
            scores.append(confidence)

    text = "\n".join(" ".join(parts) for parts in grouped)
    if not scores:
        return text, 0.0
    return text, round(sum(scores) / len(scores) / 100.0, 4)


def _open_document(path: str) -> pymupdf.Document:
    """Open ``path`` as a PDF or image, reporting failures with the filename.

    PyMuPDF opens PDFs and raster images (JPG/PNG/...) with the same call, so
    phone photos of a deed work as well as a scanned PDF. Any open failure
    (missing file, corrupt data, unsupported container) becomes a
    ``RuntimeError`` naming the file, which is what the pipeline surfaces to the
    user.
    """
    try:
        return pymupdf.open(path)
    except Exception as exc:  # pymupdf raises FileNotFoundError / RuntimeError / ...
        raise RuntimeError(f"Could not open {path!r} for OCR: {exc}") from exc


class TesseractOcrService:
    """OCR engine backed by the local Tesseract binary (via pytesseract)."""

    @property
    def engine_version(self) -> str:
        """``"tesseract-<version>"`` (``"tesseract-unknown"`` when unavailable)."""
        return f"tesseract-{_engine_version_string()}"

    def extract(self, path: str, languages: list[str]) -> OcrResult:
        """Extract the text of every page of ``path`` (PDF or image).

        ``languages`` are PropChain labels ("marathi"/"english"/...); they only
        affect the pages that need Tesseract. Raises ``RuntimeError`` for an
        unreadable document, a password-protected PDF, or a missing Tesseract
        binary.
        """
        language_string = tesseract_language_string(languages)
        pages: list[OcrPage] = []

        document = _open_document(path)
        try:
            if document.needs_pass:
                raise RuntimeError(
                    f"Could not OCR {path!r}: the document is password protected."
                )
            if document.page_count == 0:
                raise RuntimeError(f"Could not OCR {path!r}: the document has no pages.")
            for page in document:
                page_number = page.number + 1
                text_layer = (page.get_text("text") or "").strip()
                if len(text_layer) >= TEXT_LAYER_MIN_CHARS:
                    logger.debug("Page %s of %s has a text layer; skipping OCR", page_number, path)
                    pages.append(OcrPage(page_number=page_number, text=text_layer, confidence=None))
                else:
                    pages.append(self._ocr_page(page, page_number, path, language_string))
        finally:
            document.close()

        combined = "\n".join(page.text for page in pages)
        return OcrResult(
            pages=pages,
            language=detect_language(combined),
            engine_version=self.engine_version,
        )

    def _ocr_page(
        self,
        page: pymupdf.Page,
        page_number: int,
        path: str,
        language_string: str,
    ) -> OcrPage:
        """Rasterize, preprocess and OCR one page of a scanned document."""
        _ensure_tesseract_available()
        try:
            pixmap = page.get_pixmap(dpi=settings.ocr_dpi)
        except Exception as exc:
            raise RuntimeError(
                f"Could not rasterize page {page_number} of {path!r}: {exc}"
            ) from exc

        gray = image_prep.to_gray(_pixmap_to_bgr(pixmap))
        gray = image_prep.deskew(gray)
        gray = image_prep.enhance_contrast(gray)

        try:
            data = pytesseract.image_to_data(
                gray,
                lang=language_string,
                config=tesseract_config(),
                output_type=Output.DICT,
            )
        except TesseractNotFoundError as exc:
            raise RuntimeError(
                f"Tesseract binary not found while OCR-ing {path!r} "
                f"(page {page_number}). {_TESSERACT_HINT}"
            ) from exc
        except TesseractError as exc:
            raise RuntimeError(
                f"Tesseract failed on page {page_number} of {path!r}: {exc}. "
                "Check OCR_LANGS, TESSDATA_PREFIX and that the required "
                "traineddata files exist."
            ) from exc

        text, confidence = _assemble_page_text(data)
        logger.debug(
            "OCR page %s of %s: %s characters, confidence %.3f",
            page_number,
            path,
            len(text),
            confidence,
        )
        return OcrPage(page_number=page_number, text=text, confidence=confidence)
