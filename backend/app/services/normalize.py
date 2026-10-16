"""Normalization helpers for the Phase 2 extraction pipeline.

Pure stdlib (rapidfuzz is an optional accelerator for :func:`name_similarity`).
Every function is deterministic and side-effect free; the pattern extractor
(``app.services.nlp_patterns``) and the accuracy harness reuse them, so
"normalized" means the same thing everywhere.

Conventions:
- Devanagari digits are folded to ASCII before any numeric parsing.
- Dates normalize to ISO ``YYYY-MM-DD`` and validate against the real calendar —
  an impossible date yields None, never a guessed correction.
- Areas normalize to the ``AreaUnit`` vocabulary (sqft/sqm/guntha/acre/hectare);
  square yards convert to square feet because the vocabulary has no sq yd.
- Names keep their script; honorifics are stripped for display and comparison.
"""

from __future__ import annotations

import re
from datetime import date

try:  # optional accelerator; the module stays importable without rapidfuzz
    from rapidfuzz import fuzz as _fuzz
except ImportError:  # pragma: no cover - exercised only on bare installs
    _fuzz = None

# --------------------------------------------------------------------------
# Digits / whitespace
# --------------------------------------------------------------------------

#: Devanagari digits U+0966..U+096F -> ASCII.
_DEVANAGARI_DIGITS = {chr(0x0966 + i): str(i) for i in range(10)}
_DIGIT_TABLE = str.maketrans(_DEVANAGARI_DIGITS)


def devanagari_digits_to_ascii(text: str) -> str:
    """Fold Devanagari digits (०-९) to ASCII (0-9); other characters pass through."""
    return text.translate(_DIGIT_TABLE)


def normalize_whitespace(text: str | None) -> str:
    """Collapse runs of whitespace to single spaces and trim."""
    return re.sub(r"\s+", " ", text or "").strip()


# --------------------------------------------------------------------------
# Names
# --------------------------------------------------------------------------

_HONORIFIC = re.compile(
    r"(?:^|\s)(?:श्रीमती|श्री|सौ|कु|डॉ|Smt|Shri|Shree|Mrs|Mr|Ms|Dr)\.?\s+",
    re.IGNORECASE,
)


def strip_honorifics(name: str) -> str:
    """Remove leading/mid-string honorifics ("श्री. सुरेश देशमुख" -> "सुरेश देशमुख")."""
    text = normalize_whitespace(name)
    previous = None
    while previous != text:  # "Smt. Mrs. X" style double honorifics
        previous = text
        text = _HONORIFIC.sub(" ", text)
    return normalize_whitespace(text)


def normalize_person_key(name: str) -> str:
    """Comparison key for person names: honorifics off, casefolded, punctuation dropped.

    Keeps Devanagari letters *and* combining marks (U+0900-U+097F) explicitly —
    ``\\w`` alone does not match matras, which would shred Marathi names.
    """
    text = strip_honorifics(name).casefold()
    text = re.sub(r"[^\w\u0900-\u097F ]+", " ", text)
    text = text.replace("\u0964", " ").replace("\u0965", " ")  # danda / double danda
    return normalize_whitespace(text)


def name_similarity(left: str, right: str) -> float:
    """0-100 similarity of two person names (honorific/case/punctuation-insensitive)."""
    key_left, key_right = normalize_person_key(left), normalize_person_key(right)
    if not key_left or not key_right:
        return 0.0
    if _fuzz is not None:
        return float(_fuzz.token_set_ratio(key_left, key_right))
    import difflib  # pragma: no cover - fallback only

    return 100.0 * difflib.SequenceMatcher(None, key_left, key_right).ratio()


# --------------------------------------------------------------------------
# Amounts
# --------------------------------------------------------------------------

_AMOUNT_TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?")
_LAKH = re.compile(r"lakh|lac\b|लाख|लक्ष", re.IGNORECASE)
_CRORE = re.compile(r"crore|करोड|कोटी", re.IGNORECASE)


def parse_amount(text: str | None) -> float | None:
    """First monetary amount in the text, normalised to plain rupees.

    Handles Indian digit grouping ("12,50,000"), currency markers (Rs/Rs./₹/रु)
    and the lakh/crore (लाख/करोड) multipliers: "12.5 लाख" -> 1250000.0.
    """
    if not text:
        return None
    folded = devanagari_digits_to_ascii(text)
    match = _AMOUNT_TOKEN.search(folded)
    if not match:
        return None
    try:
        value = float(match.group(0).replace(",", ""))
    except ValueError:
        return None
    if _CRORE.search(folded):
        value *= 1e7
    elif _LAKH.search(folded):
        value *= 1e5
    return value


# --------------------------------------------------------------------------
# Areas
# --------------------------------------------------------------------------

#: Square-foot conversion factors — the single source of truth (mirrored as
#: literals in ``scripts/make_fixtures.py`` for the labelled ground truth).
SQFT_CONVERSIONS: dict[str, float] = {
    "sqft": 1.0,
    "sqyd": 9.0,
    "sqm": 10.7639,
    "guntha": 1089.0,
    "acre": 43560.0,
    "hectare": 107639.0,
}

#: Units the DB vocabulary (``AreaUnit``) can store.
CANONICAL_AREA_UNITS = ("sqft", "sqm", "guntha", "acre", "hectare")

_AREA_UNIT_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("sqft", ("sq. ft.", "sq.ft.", "sq.ft", "sq ft", "sqft", "square feet", "चौ.फूट", "चौ.फू.", "चौ.फू", "चौरस फूट", "चौरस फुट")),
    ("sqm", ("sq.m.", "sq.m", "sq m", "sqm", "square meters", "square meter", "चौ.मी.", "चौ.मी", "चौरस मीटर")),
    ("sqyd", ("sq.yd.", "sq.yd", "sq yd", "sqyd", "चौ.गज", "चौरस गज", "गज")),
    ("guntha", ("guntha", "gunthas", "गुंठा", "गुंठे", "गुंठ")),
    ("hectare", ("hectare", "hectares", "हेक्टर", "हेक्टेअर", "हे.आर.", "हे.आर", "हे आर", "हे.", "ha")),
    ("acre", ("acre", "acres", "एकर")),
)


def _build_unit_regex() -> tuple[re.Pattern[str], dict[str, str]]:
    pairs: list[tuple[str, str]] = []
    for canonical, aliases in _AREA_UNIT_ALIASES:
        pairs.extend((alias, canonical) for alias in aliases)
    pairs.sort(key=lambda pair: len(pair[0]), reverse=True)  # longest alias first
    alternation = "|".join(re.escape(alias) for alias, _ in pairs)
    pattern = re.compile(
        r"(?<![\w\u0900-\u097F])(?P<unit>" + alternation + r")(?![\w\u0900-\u097F])",
        re.IGNORECASE,
    )
    return pattern, dict(pairs)


_UNIT_RE, _UNIT_LOOKUP = _build_unit_regex()
_NUMBER = r"(?P<value>\d+(?:[.,]\d+)?)"
_AREA_AFTER = re.compile(_NUMBER + r"\s*(?:" + _UNIT_RE.pattern + r")", re.IGNORECASE)
_AREA_BEFORE = re.compile(_UNIT_RE.pattern + r"\s*[:：]?\s*" + _NUMBER, re.IGNORECASE)


def parse_area(text: str | None) -> tuple[float, str] | None:
    """First area with a recognised unit: ("124 गुंठा" -> (124.0, "guntha")).

    Accepts value-then-unit and unit-then-value forms and either digit script.
    Returns the raw number with its canonical unit token (including "sqyd" —
    the extractor converts that via :func:`canonicalize_area`).
    """
    if not text:
        return None
    folded = normalize_whitespace(devanagari_digits_to_ascii(text))
    for pattern in (_AREA_AFTER, _AREA_BEFORE):
        match = pattern.search(folded)
        if not match:
            continue
        raw_value = match.group("value").replace(",", "")
        try:
            value = float(raw_value)
        except ValueError:
            continue
        unit = _UNIT_LOOKUP.get(match.group("unit").casefold())
        if unit:
            return value, unit
    return None


def to_sqft(value: float, unit: str | None) -> float | None:
    """Convert an area to square feet; None for unknown units."""
    factor = SQFT_CONVERSIONS.get((unit or "").casefold())
    if factor is None:
        return None
    return value * factor


def canonicalize_area(value: float, unit: str | None) -> tuple[float, str] | None:
    """Map onto the ``AreaUnit`` vocabulary; sq yd converts to sq ft, others pass."""
    unit = (unit or "").casefold()
    if unit == "sqyd":
        return value * SQFT_CONVERSIONS["sqyd"], "sqft"
    if unit in CANONICAL_AREA_UNITS:
        return value, unit
    return None


# --------------------------------------------------------------------------
# Dates
# --------------------------------------------------------------------------

_MONTHS: dict[str, int] = {
    "january": 1, "jan": 1, "जानेवारी": 1, "जाने": 1,
    "february": 2, "feb": 2, "फेब्रुवारी": 2, "फेब्रु": 2,
    "march": 3, "mar": 3, "मार्च": 3,
    "april": 4, "apr": 4, "एप्रिल": 4,
    "may": 5, "मे": 5,
    "june": 6, "jun": 6, "जून": 6,
    "july": 7, "jul": 7, "जुलै": 7,
    "august": 8, "aug": 8, "ऑगस्ट": 8,
    "september": 9, "sep": 9, "sept": 9, "सप्टेंबर": 9,
    "october": 10, "oct": 10, "ऑक्टोबर": 10,
    "november": 11, "nov": 11, "नोव्हेंबर": 11,
    "december": 12, "dec": 12, "डिसेंबर": 12,
}

_MONTH_ALT = "|".join(sorted(_MONTHS, key=len, reverse=True))

_DMY = re.compile(r"(?<![\d/])(?P<a>\d{1,2})\s*[/\-.]\s*(?P<b>\d{1,2})\s*[/\-.]\s*(?P<y>\d{2,4})(?![\d/])")
_ISO = re.compile(r"\b(?P<y>\d{4})\s*-\s*(?P<m>\d{1,2})\s*-\s*(?P<d>\d{1,2})\b")
_D_TEXT_Y = re.compile(
    r"\b(?P<d>\d{1,2})(?:st|nd|rd|th)?\s*(?:of\s+)?(?P<mon>" + _MONTH_ALT + r")\s*,?\s*(?P<y>\d{2,4})\b",
    re.IGNORECASE,
)
_TEXT_D_Y = re.compile(
    r"\b(?P<mon>" + _MONTH_ALT + r")\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(?P<y>\d{2,4})\b",
    re.IGNORECASE,
)


def _expand_year(raw: str) -> int:
    year = int(raw)
    if len(raw) <= 2:
        return 2000 + year if year <= 49 else 1900 + year
    return year


def _iso_or_none(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:  # impossible calendar date (31/02/2019, month 13, ...)
        return None


def parse_iso_date(text: str | None) -> str | None:
    """First valid calendar date in the text as ISO ``YYYY-MM-DD``, else None.

    Supports dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy, yyyy-mm-dd, "15 March 2019",
    "15th March 2019", "March 15, 2019" and the Marathi month names, in either
    digit script. Ambiguous slash dates follow the Indian dd/mm convention;
    impossible dates are skipped, never "fixed".
    """
    if not text:
        return None
    folded = normalize_whitespace(devanagari_digits_to_ascii(text))
    matches: list[tuple[int, str | None]] = []

    for match in _ISO.finditer(folded):
        matches.append(
            (
                match.start(),
                _iso_or_none(int(match.group("y")), int(match.group("m")), int(match.group("d"))),
            )
        )

    for match in _DMY.finditer(folded):
        a, b, year = int(match.group("a")), int(match.group("b")), _expand_year(match.group("y"))
        day, month = a, b
        if day <= 12 and b > 12:  # unambiguous mm/dd-style pair (05/13 -> 13 May)
            day, month = b, a
        matches.append((match.start(), _iso_or_none(year, month, day)))

    for pattern in (_D_TEXT_Y, _TEXT_D_Y):
        for match in pattern.finditer(folded):
            month = _MONTHS.get(match.group("mon").casefold())
            if month is None:
                continue
            matches.append(
                (
                    match.start(),
                    _iso_or_none(_expand_year(match.group("y")), month, int(match.group("d"))),
                )
            )

    for _, iso in sorted(matches, key=lambda item: item[0]):
        if iso:
            return iso
    return None


# --------------------------------------------------------------------------
# Identifiers
# --------------------------------------------------------------------------

_IDENT_CLEAN = re.compile(r"[^0-9A-Z\u0900-\u097F/\-]")


def normalize_identifier(value: str | None) -> str:
    """Uppercase, keep alphanumerics (both scripts), "/" and "-": "124 / अ" -> "124/अ"."""
    folded = devanagari_digits_to_ascii(value or "").upper()
    return _IDENT_CLEAN.sub("", folded)


def normalize_registration_number(value: str | None) -> str:
    """Uppercase and drop separators/spaces: "mh-pun-2019-12345" -> "MH-PUN-2019-12345"."""
    folded = devanagari_digits_to_ascii(value or "").upper()
    return re.sub(r"[^0-9A-Z\u0900-\u097F/\-]", "", folded)


# --------------------------------------------------------------------------
# Script profile (used for language detection and diagnostics)
# --------------------------------------------------------------------------


def script_profile(text: str | None) -> tuple[int, int]:
    """Count (Devanagari characters, Latin letters) in the text."""
    devanagari = latin = 0
    for char in text or "":
        if "\u0900" <= char <= "\u097f":
            devanagari += 1
        elif char.isascii() and char.isalpha():
            latin += 1
    return devanagari, latin
