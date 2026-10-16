"""Pattern-based field extraction — the Phase 2 real NLP engine.

Project-defined rule set: label regexes (English + Marathi) over OCR text with
normalization in ``app.services.normalize``. No training data, no ML model.

Honesty rules:
- a candidate is emitted only when the captured value validates (a real
  calendar date, a parseable amount/area, a plausible name/identifier);
- absent evidence yields no candidate — the pipeline stores "unknown" by
  omission, never an invented value.

Pages: ``ocr_text`` separates pages with the form-feed character ``chr(12)``
(see ``app.services.interfaces``); candidates carry the 1-based page where the
value was found. Within a page the first label match that yields a *valid*
value wins; standalone patterns (registration numbers, marked dates, bare
areas) are consulted only for fields still missing.
"""

from __future__ import annotations

import re
from functools import lru_cache

from app.services import normalize
from app.services.fields import CANONICAL_FIELDS, value_type_for
from app.services.interfaces import FieldCandidate

ENGINE_VERSION = "patterns-v1"
PAGE_SEPARATOR = "\f"

#: Confidence defaults (deterministic, documented).
CONF_LABEL = 0.90
CONF_LABEL_NAME = 0.88
CONF_PATTERN = 0.65

# ---------------------------------------------------------------------------
# Label vocabulary: field -> regex fragments (project-defined heuristics).
# ---------------------------------------------------------------------------

_COMMON_LABELS: dict[str, tuple[str, ...]] = {
    "owner_name": (
        r"owner(?:'s)? name",
        r"name of (?:the )?owner",
        r"holder(?:'s)? name",
        r"owner",
        r"holder",
        r"धारकाचे नाव",
        r"मालकाचे नाव",
        r"खातेदार",
        r"धारक",
        r"मालक",
    ),
    "seller_name": (
        r"विक्री करणारे",
        r"विक्री करणारा",
        r"विक्रेत्याचे नाव",
        r"विक्रेता",
        r"vendor",
        r"seller",
        r"transferor",
    ),
    "buyer_name": (
        r"खरेदीदाराचे नाव",
        r"खरेदी करणारे",
        r"खरेदी करणारा",
        r"खरेदीदार",
        r"vendee",
        r"purchaser",
        r"buyer",
        r"transferee",
    ),
    "survey_number": (
        r"survey (?:no|number)",
        r"s\.?\s*no\.?",
        r"सर्व्हे (?:नं|क्र)",
        r"स\.?\s*नं\.?",
        r"भूमापन (?:क्र|नं)",
    ),
    "gat_number": (
        r"gat (?:no|number)\.?",
        r"गट क्रमांक",
        r"गट (?:क्र|नं)\.?",
    ),
    "cts_number": (
        r"cts (?:no|number)\.?",
        r"सिटी सर्व्हे (?:नं|क्र)\.?",
        r"सी\.?\s*टी\.?\s*एस\.?",
    ),
    "ulpin": (r"ulpin", r"युपिन", r"युलपिन"),
    "village": (r"village", r"गाव"),
    "taluka": (r"taluka", r"taluk", r"तालुका"),
    "district": (r"district", r"जिल्हा"),
    "registration_number": (
        r"registration (?:no|number)",
        r"reg(?:istration)?\.?\s*no\.?",
        r"नोंदणी क्रमांक",
        r"नोंदणी नं",
    ),
    "registration_date": (
        r"registration date",
        r"date of registration",
        r"नोंदणी दिनांक",
    ),
    "execution_date": (
        r"date of execution",
        r"execution date",
        r"executed on",
        r"दस्तऐवज दिनांक",
        r"कार्यवाही दिनांक",
        r"अंमलबजावणी दिनांक",
    ),
    "consideration_amount": (
        r"consideration(?: amount| price| value)?",
        r"sale (?:price|consideration)",
        r"विक्री किंमत",
        r"मोबदला",
        r"रक्कम",
    ),
    "boundaries": (r"boundaries", r"boundary", r"सीमा", r"हद्दी", r"हद्द"),
    "referred_document": (
        r"predecessor(?: document| deed)?",
        r"previous (?:document|deed)",
        r"संदर्भित दस्तऐवज",
        r"पूर्वीचे (?:दस्तऐवज|खत)",
        r"पूर्वीचे खरेदीखत",
        r"मागील (?:खत|दस्तऐवज)",
    ),
}

_AREA_LABELS: tuple[str, ...] = (r"total area", r"area", r"एकूण क्षेत्र", r"क्षेत्र")

#: Doc-type specific label additions/overrides (kept tiny on purpose).
_DOC_LABELS: dict[str, dict[str, tuple[str, ...]]] = {
    "gift_deed": {
        "seller_name": (r"donor", r"देणगीदार", r"देणगी देणारे", r"देणगी देणारा"),
        "buyer_name": (r"donee", r"देणगी घेणारे", r"देणगी घेणारा", r"देणी घेणारे", r"देणी घेणारा", r"बक्षीस घेणारे"),
    },
    "mortgage_deed": {
        "seller_name": (r"mortgagor", r"गहाण ठेवणारे", r"तारण ठेवणारे"),
        "buyer_name": (r"mortgagee", r"गहाण घेणारे", r"तारण घेणारे", r"bank"),
    },
    "lease_deed": {
        "seller_name": (r"lessor", r"landlord", r"भाडे देणारे"),
        "buyer_name": (r"lessee", r"tenant", r"भाडे घेणारे"),
    },
    "will": {
        "owner_name": (
            r"testator",
            r"testatrix",
            r"मृत्युपत्र करणारे",
            r"इच्छापत्र करणारे",
        ),
    },
    "7_12_extract": {
        "owner_name": (r"अधिकार धारक", r"खातेदार", r"धारक", r"मालक"),
    },
    "property_card": {
        "owner_name": (r"owner(?:'s)? name", r"मालकाचे नाव", r"मालक"),
    },
    "ferfar": {
        # The ferfar register entry date is the mutation date (see the fixture notes).
        "registration_date": (r"mutation date", r"फेरफार दिनांक"),
    },
}

#: Which fields are plausible for each document type (roadmap subset).
_FIELDS_BY_DOC_TYPE: dict[str, tuple[str, ...]] = {
    "sale_deed": (
        "seller_name", "buyer_name", "survey_number", "gat_number", "cts_number",
        "village", "taluka", "district", "area", "registration_number",
        "registration_date", "execution_date", "consideration_amount",
        "boundaries", "referred_document",
    ),
    "agreement_to_sale": (
        "seller_name", "buyer_name", "survey_number", "gat_number", "village",
        "taluka", "district", "area", "consideration_amount", "execution_date",
        "boundaries", "referred_document",
    ),
    "gift_deed": (
        "seller_name", "buyer_name", "survey_number", "village", "taluka",
        "district", "area", "consideration_amount", "registration_number",
        "registration_date", "boundaries", "referred_document",
    ),
    "mortgage_deed": (
        "seller_name", "buyer_name", "survey_number", "village", "taluka",
        "district", "area", "registration_number", "registration_date",
        "consideration_amount", "referred_document",
    ),
    "lease_deed": (
        "seller_name", "buyer_name", "survey_number", "village", "taluka",
        "district", "area", "registration_date", "execution_date",
        "consideration_amount",
    ),
    "partition_deed": (
        "survey_number", "village", "taluka", "district", "area",
        "registration_number", "registration_date", "boundaries",
        "referred_document",
    ),
    "will": (
        "owner_name", "survey_number", "village", "taluka", "district", "area",
        "execution_date", "referred_document",
    ),
    "7_12_extract": (
        "owner_name", "survey_number", "gat_number", "ulpin", "village",
        "taluka", "district", "area",
    ),
    "8a_record": (
        "owner_name", "survey_number", "village", "taluka", "district", "area",
    ),
    "ferfar": (
        "owner_name", "survey_number", "village", "district", "area",
        "registration_number", "registration_date", "referred_document",
    ),
    "property_card": (
        "owner_name", "survey_number", "cts_number", "ulpin", "village",
        "district", "area", "boundaries",
    ),
    "ec": (
        "owner_name", "survey_number", "cts_number", "village", "district",
        "area", "registration_number", "registration_date", "referred_document",
    ),
    "rera": (
        "seller_name", "buyer_name", "village", "district", "area",
        "registration_number", "registration_date", "consideration_amount",
    ),
    "court_document": (
        "owner_name", "survey_number", "village", "district",
        "registration_date", "referred_document",
    ),
}

_AREA_GROUP = ("area", "area_unit", "area_sqft")

_NAME_FIELDS = frozenset({"owner_name", "seller_name", "buyer_name"})
_IDENT_FIELDS = frozenset({"survey_number", "gat_number", "cts_number", "ulpin"})
_DATE_FIELDS = frozenset({"registration_date", "execution_date"})

#: Standalone patterns (used only when the labelled pass found nothing).
_MH_REGISTRATION = re.compile(
    r"(?<![\w\-])(?P<reg>[A-Za-z]{1,4}(?:[-/][A-Za-z]{1,4})?[-/]\d{4}[-/]\d{3,7})(?![\w])"
)
_DATE_LINE_MARKER = re.compile(r"नोंदणी|registration|दिनांक|dated|date of|date:", re.IGNORECASE)
_REGISTRATION_MARKER = re.compile(r"नोंदणी|registration", re.IGNORECASE)

#: Stop-words for text values that would otherwise swallow the next label.
_TEXT_STOP = re.compile(
    r"(?<![\w\u0900-\u097F])(?:गाव|तालुका|जिल्हा|village|taluka|taluk|district)(?![\w\u0900-\u097F])",
    re.IGNORECASE,
)

#: Unicode spaces (NBSP, thin/figure space, ideographic space, ...) that text
#: layers and OCR output use instead of U+0020 and that would otherwise break
#: label patterns ("Survey\u00a0No." is not "Survey No.").  \n and \f are kept.
_UNICODE_SPACES = re.compile(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]")

#: Zero-width / invisible characters OCR inserts inside Devanagari clusters
#: (e.g. "हेक्\u200dटर").  Removing them is lossless for matching.
_INVISIBLE = re.compile(r"[\u200b\u200c\u200d\ufeff\u2060]")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


@lru_cache(maxsize=None)
def _compiled_label(label: str) -> re.Pattern[str]:
    return re.compile(
        r"(?<![\w\u0900-\u097F])(?:" + label + r")(?![\w\u0900-\u097F])[\s:：\-–—]*"
        r"(?P<value>[^\n]{1,160})",
        re.IGNORECASE,
    )


@lru_cache(maxsize=None)
def _labels_for(field: str, doc_type: str) -> tuple[str, ...]:
    labels = list(_COMMON_LABELS.get(field, ()))
    labels.extend(_DOC_LABELS.get(doc_type, {}).get(field, ()))
    return tuple(labels)


def _fields_for(doc_type: str) -> tuple[str, ...]:
    allowed = _FIELDS_BY_DOC_TYPE.get((doc_type or "unknown").lower())
    if allowed is None:  # unknown/other: conservative union sweep
        union: set[str] = set()
        for fields in _FIELDS_BY_DOC_TYPE.values():
            union.update(fields)
        allowed = tuple(union)
    allowed = set(allowed)
    if "area" in allowed:
        allowed.update(_AREA_GROUP)
    return tuple(field for field in CANONICAL_FIELDS if field in allowed)


def _snippet(text: str, position: int) -> str:
    start = text.rfind("\n", 0, position) + 1
    end = text.find("\n", position)
    line = text[start:] if end == -1 else text[start:end]
    return normalize.normalize_whitespace(line)[:120]


def _cut(value: str, *, commas: bool = False) -> str:
    """Trim a raw captured value at separators and surrounding punctuation."""
    text = value
    for separator in ("|", ";", "  "):
        index = text.find(separator)
        if index != -1:
            text = text[:index]
    if commas:
        index = text.find(",")
        if index != -1:
            text = text[:index]
    return text.strip().strip(".:-–—•*/ ")


def _drop_label_prefix(value: str) -> str:
    """Keep the text after the first colon when a captured value still starts
    with the next label of a combined row ("Vendor / Seller: X" -> "X")."""
    if ":" in value:
        return value.split(":", 1)[1]
    return value


def _clean_name(value: str) -> str | None:
    text = normalize.normalize_whitespace(value)
    text = re.sub(r"^(?:name|नाव|नाम)\s*[:：]\s*", "", text, flags=re.IGNORECASE)
    text = normalize.strip_honorifics(text)
    if len(text) < 2 or len(text) > 80:
        return None
    if any(char.isdigit() for char in text):
        return None
    if len(text.split()) > 6:
        return None
    if not any("\u0900" <= char <= "\u097f" or char.isalpha() for char in text):
        return None
    return text


def _first_identifier_token(value: str) -> str | None:
    for match in re.finditer(r"[0-9A-Za-z\u0900-\u097F]+(?:[/\-.][0-9A-Za-z\u0900-\u097F]+)*", value):
        token = match.group(0)
        folded = normalize.devanagari_digits_to_ascii(token)
        if any(char.isdigit() for char in folded):
            return token
    return None


def _num_str(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def _candidate(
    field: str,
    raw: str,
    normalized: str,
    confidence: float,
    page: int,
    snippet: str,
) -> FieldCandidate:
    return FieldCandidate(
        field_name=field,
        raw_value=raw or None,
        value_type=value_type_for(field),
        confidence=confidence,
        page=page,
        snippet=snippet,
        normalized_value=normalized or None,
    )


def _area_field_candidates(
    value: float,
    unit: str,
    raw: str,
    page: int,
    snippet: str,
    confidence: float,
) -> list[FieldCandidate]:
    """area + area_unit (+ derived area_sqft) from one parsed value/unit pair."""
    canonical = normalize.canonicalize_area(value, unit)
    if canonical is None:
        return []
    area_value, area_unit = canonical
    candidates = [
        _candidate("area", raw, _num_str(area_value), confidence, page, snippet),
        _candidate("area_unit", raw, area_unit, confidence, page, snippet),
    ]
    square_feet = normalize.to_sqft(area_value, area_unit)
    if square_feet is not None:
        candidates.append(
            _candidate("area_sqft", raw, _num_str(square_feet), confidence, page, snippet)
        )
    return candidates


# ---------------------------------------------------------------------------
# Value post-processing per field kind
# ---------------------------------------------------------------------------


def _registration_token(value: str) -> str | None:
    match = _MH_REGISTRATION.search(value)
    if match:
        return match.group("reg")
    return _first_identifier_token(value)


def _postprocess(field: str, value: str) -> tuple[str, str] | None:
    """(raw as printed, normalized) for a captured value, or None if invalid."""
    if field in _NAME_FIELDS:
        raw = _cut(_drop_label_prefix(value), commas=True)
        cleaned = _clean_name(raw)
        if cleaned is None:
            return None
        return raw, cleaned

    if field in _IDENT_FIELDS or field == "registration_number":
        if field == "registration_number":
            token = _registration_token(value)
            if token is None:
                return None
            return token, normalize.normalize_registration_number(token)
        if field == "gat_number" and re.search(r"\s/\s", value):
            # Combined rows ("Survey No. / Gat No.: 124/A / 456"): the Gat value
            # is the token after the last spaced slash.
            token = _first_identifier_token(value.rsplit(" / ", 1)[-1])
        else:
            token = _first_identifier_token(value)
        if token is None:
            return None
        return token, normalize.normalize_identifier(token)

    if field in _DATE_FIELDS:
        iso = normalize.parse_iso_date(value)
        if iso is None:
            return None
        return _cut(value)[:60], iso

    if field == "consideration_amount":
        raw = _cut(_drop_label_prefix(value))
        amount = normalize.parse_amount(raw)
        if amount is None:
            return None
        return raw[:60], _num_str(amount)

    # Text fields (village/taluka/district/boundaries/referred_document).
    raw = _cut(_drop_label_prefix(value) if field in {"village", "taluka", "district"} else value)
    if field in {"village", "taluka", "district"}:
        stop = _TEXT_STOP.search(raw)
        if stop:
            raw = raw[: stop.start()].strip()
    if len(raw) < 2:
        return None
    return raw, raw


# ---------------------------------------------------------------------------
# Extraction passes
# ---------------------------------------------------------------------------


def _labelled_hit(
    field: str, doc_type: str, page_text: str
) -> tuple[str, str, float, int, str] | None:
    """(raw, normalized, confidence, offset, snippet) for the first valid label match."""
    confidence = CONF_LABEL_NAME if field in _NAME_FIELDS else CONF_LABEL
    for label in _labels_for(field, doc_type):
        for match in _compiled_label(label).finditer(page_text):
            result = _postprocess(field, match.group("value"))
            if result is None:
                continue
            raw, normalized = result
            return raw, normalized, confidence, match.start(), _snippet(page_text, match.start())
    return None


def _labelled_area(doc_type: str, page_text: str) -> list[FieldCandidate]:
    for label in _AREA_LABELS:
        for match in _compiled_label(label).finditer(page_text):
            parsed = normalize.parse_area(match.group("value"))
            if parsed is None:
                continue
            value, unit = parsed
            candidates = _area_field_candidates(
                value, unit, _cut(match.group("value"))[:60], 1, _snippet(page_text, match.start()), CONF_LABEL
            )
            if candidates:
                return candidates
    return []


def _standalone_hits(field: str, page_text: str) -> list[tuple[str, str, float, str]]:
    """(raw, normalized, confidence, snippet) matches without a label."""
    if field == "registration_number":
        match = _MH_REGISTRATION.search(page_text)
        if match:
            raw = match.group("reg")
            return [(raw, normalize.normalize_registration_number(raw), CONF_PATTERN, _snippet(page_text, match.start()))]

    if field in _DATE_FIELDS:
        for line in page_text.splitlines():
            if not _DATE_LINE_MARKER.search(line):
                continue
            iso = normalize.parse_iso_date(line)
            if iso is None:
                continue
            target = "registration_date" if _REGISTRATION_MARKER.search(line) else "execution_date"
            if target != field:
                continue
            return [(_cut(line)[:60], iso, CONF_PATTERN, normalize.normalize_whitespace(line)[:120])]

    return []


def _standalone_area(page_text: str) -> list[FieldCandidate]:
    for line in page_text.splitlines():
        parsed = normalize.parse_area(line)
        if parsed is None:
            continue
        value, unit = parsed
        candidates = _area_field_candidates(
            value, unit, _cut(line)[:60], 1, normalize.normalize_whitespace(line)[:120], CONF_PATTERN
        )
        if candidates:
            return candidates
    return []


class PatternNLPExtractor:
    """NLPExtractor implementation with ``engine_version = "patterns-v1"``."""

    engine_version = ENGINE_VERSION

    def extract(self, doc_type: str, ocr_text: str) -> list[FieldCandidate]:
        # Text layers and OCR can emit Unicode spaces instead of U+0020 and
        # zero-width joiners inside clusters (see _UNICODE_SPACES/_INVISIBLE);
        # fold/remove them before any label matching.
        cleaned = _INVISIBLE.sub("", ocr_text or "")
        pages = _UNICODE_SPACES.sub(" ", cleaned).split(PAGE_SEPARATOR)
        wanted = _fields_for(doc_type)
        found: dict[str, FieldCandidate] = {}

        # Pass A — labelled values (highest confidence), page order first.
        for page_number, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue
            for field in wanted:
                if field in found or field in ("area_unit", "area_sqft"):
                    continue
                if field == "area":
                    area_candidates = _labelled_area(doc_type, page_text)
                    for candidate in area_candidates:
                        candidate.page = page_number
                        found[candidate.field_name] = candidate
                    continue
                hit = _labelled_hit(field, doc_type, page_text)
                if hit is None:
                    continue
                raw, normalized, confidence, _offset, snippet = hit
                found[field] = _candidate(field, raw, normalized, confidence, page_number, snippet)

        # Pass B — standalone patterns for whatever is still missing.
        for page_number, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue
            for field in wanted:
                if field in found or field in ("area_unit", "area_sqft"):
                    continue
                if field == "area":
                    area_candidates = _standalone_area(page_text)
                    for candidate in area_candidates:
                        candidate.page = page_number
                        found[candidate.field_name] = candidate
                    continue
                for raw, normalized, confidence, snippet in _standalone_hits(field, page_text):
                    found[field] = _candidate(field, raw, normalized, confidence, page_number, snippet)
                    break

        return [found[field] for field in CANONICAL_FIELDS if field in found]
