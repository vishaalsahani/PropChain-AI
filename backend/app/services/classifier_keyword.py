"""Deterministic keyword/regex document classifier ("keyword-v1").

Phase 2 replacement for ``fakes.FakeDocClassifier``: instead of a first-match
keyword scan over the filename it scores every known document type over BOTH
the file name and the OCR text, and abstains (``"unknown"``) when the evidence
is too weak to name a type.

Design
------
* Channels: the file name (base name only, so upload folders cannot leak
  signals) is worth ``FILENAME_WEIGHT`` (2x) per signal, the OCR text
  ``TEXT_WEIGHT`` (1x). A signal seen in both channels counts in both — a
  filename that agrees with the text is genuinely more evidence. A signal
  counts once per channel no matter how often it occurs.
* Matching is case-insensitive (``str.casefold``) and Unicode-normalised (NFC,
  OCR output is often decomposed). Both channels are matched twice: as-is and
  "humanised" (``_``, ``-``, ``.`` and whitespace collapsed to single spaces),
  because file names spell phrases as ``sale_deed`` / ``sale-deed`` while the
  text spells them ``sale deed``.
* Patterns are project-defined heuristics, not a legal taxonomy: each entry is
  a plain substring (the default — fastest and unambiguous) or, when word
  separators or numeric boundaries matter, a regex. Weight ladder:
  ``W_DISTINCTIVE`` for a phrase that names exactly one document type,
  ``W_STRONG`` for a role/term that only this type uses, ``W_SUPPORTING`` for
  a term that usually indicates it, ``W_WEAK`` for generic corroboration.
  Two deliberate restrictions keep English prose out: no bare generic English
  words (bare ``"property"`` is NOT a property-card signal, unlike the fake
  classifier's ``"property"`` keyword) and a standalone ``"will"`` is only
  worth ``W_WEAK``.
* The starter signal list comes from the Phase 2 task (English + Marathi,
  Maharashtra land records) and is expected to grow; every addition must keep
  the floor/confidence invariants below true.

Confidence formula (deterministic, no randomness, no clock)
----------------------------------------------------------
``top`` = weighted score of the winning type, ``runner_up`` = score of the
second best type (0.0 when there is none), both from the shared pattern packs.

1. base  = piecewise-linear interpolation of ``top`` over
   ``_CONFIDENCE_CURVE``: 0.0 -> 0.20, 2.0 -> 0.48, 3.0 -> 0.62, 5.0 -> 0.70,
   8.0 -> 0.78, 12.0 -> 0.85, 20.0 -> 0.91, >= 30.0 -> 0.95.
   Anchors are chosen so that one distinctive signal in the text (score 3.0)
   reaches 0.62 (>= 0.60) and strong multi-signal evidence (score >= 12)
   reaches >= 0.85 (>= 0.80).
2. dominance = top / (top + runner_up) in (0, 1], and the result is multiplied
   by ``DOMINANCE_FLOOR + (1 - DOMINANCE_FLOOR) * dominance`` (1.0 when the
   winning type is unchallenged, 0.925 on an exact tie) so close calls carry a
   visibly lower confidence even though the winner is still returned.
3. clamp to ``[0.0, MAX_CONFIDENCE]`` and round to 2 decimals.

Abstention: when ``top < MIN_TOP_SCORE`` (2.0 — one distinctive signal in
either channel, or two supporting signals in the text) the result is
``"unknown"`` with confidence ``NO_SIGNAL_CONFIDENCE`` (0.20) if nothing
matched at all, or ``WEAK_ONLY_CONFIDENCE`` (0.25) if weak evidence was seen
but stayed under the floor. Both are <= 0.3 as required.

Ties are broken deterministically: higher score, then more distinct matched
signals, then ascending machine value (``doc_type``). ``"other"`` is never
emitted — it is reserved for a human reviewer; the classifier only ever
returns one of ``app.models.enums.KNOWN_DOC_TYPES``.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.models.enums import KNOWN_DOC_TYPES
from app.services.interfaces import ClassificationResult

ENGINE_VERSION = "keyword-v1"

#: A file-name signal is worth twice the same signal in the OCR text.
FILENAME_WEIGHT = 2.0
#: Per-signal weight of the OCR text channel.
TEXT_WEIGHT = 1.0
#: Weighted score below which the classifier abstains ("unknown").
MIN_TOP_SCORE = 2.0
#: Confidence is never reported above this (scan/OCR classifiers are fallible).
MAX_CONFIDENCE = 0.95
#: Confidence when no signal matched anywhere.
NO_SIGNAL_CONFIDENCE = 0.20
#: Confidence when signals were seen but stayed below MIN_TOP_SCORE.
WEAK_ONLY_CONFIDENCE = 0.25
#: Worst-case multiplier applied to an exact tie between two types.
DOMINANCE_FLOOR = 0.85

#: Weight ladder for :class:`Signal` entries (see module docstring).
W_DISTINCTIVE = 3.0
W_STRONG = 2.0
W_SUPPORTING = 1.5
W_WEAK = 1.0

#: ``(score, confidence)`` anchors, linear in between, clamped at both ends.
_CONFIDENCE_CURVE: tuple[tuple[float, float], ...] = (
    (0.0, 0.20),
    (2.0, 0.48),
    (3.0, 0.62),
    (5.0, 0.70),
    (8.0, 0.78),
    (12.0, 0.85),
    (20.0, 0.91),
    (30.0, 0.95),
)

_WORD_SEPARATORS = re.compile(r"[\s._\-\u2013\u2014]+")
_PATH_SEPARATORS = re.compile(r"[\\/]")
#: Devanagari digits, for the numeric-boundary lookarounds below.
_DIGITS = r"\d\u0966-\u096f"


@dataclass(frozen=True)
class Signal:
    """One evidence entry: a substring (default) or regex plus its weight."""

    pattern: str
    weight: float
    regex: bool = False


#: doc_type -> pattern pack. Project-defined heuristics (see module docstring).
#: Keys present here are the only types this classifier can emit; ``other`` and
#: ``unknown`` are intentionally empty.
PATTERNS: dict[str, tuple[Signal, ...]] = {
    "sale_deed": (
        Signal(r"sale[\s\-_]*deed", W_DISTINCTIVE, regex=True),
        Signal(r"deed[\s\-_]*of[\s\-_]*sale", W_DISTINCTIVE, regex=True),
        Signal("विक्रीखत", W_DISTINCTIVE),
        Signal("खरेदीखत", W_DISTINCTIVE),
        Signal("विक्रीपत्र", W_DISTINCTIVE),
        Signal("विक्रेता", W_STRONG),
        Signal("खरेदीदार", W_STRONG),
        Signal("vendor", W_STRONG),
        Signal("vendee", W_STRONG),
        Signal("consideration", W_SUPPORTING),
        Signal("मोबदला", W_SUPPORTING),
        Signal("stamp duty", W_WEAK),
        Signal(r"sub[\s\-_]*registrar", W_WEAK, regex=True),
        Signal("नोंदणी", W_WEAK),
    ),
    "agreement_to_sale": (
        Signal(r"agreement[\s\-_]*to[\s\-_]*sale", W_DISTINCTIVE, regex=True),
        Signal(r"agreement[\s\-_]*for[\s\-_]*sale", W_DISTINCTIVE, regex=True),
        Signal(r"agreement[\s\-_]*to[\s\-_]*sell", W_DISTINCTIVE, regex=True),
        Signal(r"विक्री[\s\-_]*करार", W_DISTINCTIVE, regex=True),
        Signal(r"सामंजस्य[\s\-_]*करार", W_DISTINCTIVE, regex=True),
        Signal("बयाणा", W_SUPPORTING),
        Signal("बयाना", W_SUPPORTING),
        Signal("earnest money", W_SUPPORTING),
        Signal(r"\bagreement\b", W_WEAK, regex=True),
        Signal("करार", W_WEAK),
    ),
    "gift_deed": (
        Signal(r"gift[\s\-_]*deed", W_DISTINCTIVE, regex=True),
        Signal(r"settlement[\s\-_]*deed", W_DISTINCTIVE, regex=True),
        Signal("देणगीपत्र", W_DISTINCTIVE),
        Signal("बक्षीसपत्र", W_DISTINCTIVE),
        Signal(r"देणगी[\s\-_]*खत", W_DISTINCTIVE, regex=True),
        Signal("देणगीदार", W_STRONG),
        Signal("देणगी", W_SUPPORTING),
        Signal("donor", W_SUPPORTING),
        Signal("donee", W_SUPPORTING),
        Signal("gift", W_WEAK),
        Signal("बक्षीस", W_WEAK),
    ),
    "mortgage_deed": (
        Signal("mortgage", W_DISTINCTIVE),
        Signal("mortgagor", W_STRONG),
        Signal("mortgagee", W_STRONG),
        Signal("hypothec", W_STRONG),
        Signal("गहाणखत", W_DISTINCTIVE),
        Signal("तारण", W_STRONG),
        Signal("गहाण", W_SUPPORTING),
    ),
    "lease_deed": (
        Signal(r"lease[\s\-_]*deed", W_DISTINCTIVE, regex=True),
        Signal(r"rent[\s\-_]*agreement", W_DISTINCTIVE, regex=True),
        Signal("भाडेपट्टा", W_DISTINCTIVE),
        Signal("भाडेकरार", W_DISTINCTIVE),
        Signal("पट्टा", W_STRONG),
        Signal("lessor", W_STRONG),
        Signal("lessee", W_STRONG),
        Signal(r"monthly[\s\-_]*rent", W_STRONG, regex=True),
        Signal("मासिक भाडे", W_STRONG),
        Signal(r"\blease\b", W_SUPPORTING, regex=True),
        Signal("tenancy", W_SUPPORTING),
        Signal("भाडे", W_SUPPORTING),
        Signal("भाडेकरू", W_SUPPORTING),
        Signal(r"\brent\b", W_WEAK, regex=True),
    ),
    "partition_deed": (
        Signal("partition", W_DISTINCTIVE),
        Signal("वाटणीपत्र", W_DISTINCTIVE),
        Signal("फाळणीपत्र", W_DISTINCTIVE),
        Signal("coparcener", W_STRONG),
        Signal(r"joint[\s\-_]*family", W_STRONG, regex=True),
        Signal("फाळणी", W_STRONG),
        Signal(r"\bshare\b", W_SUPPORTING, regex=True),
        Signal("वाटप", W_SUPPORTING),
        Signal("हिस्सा", W_SUPPORTING),
    ),
    "will": (
        Signal(r"will[\s\-_]*deed", W_DISTINCTIVE, regex=True),
        Signal("testament", W_DISTINCTIVE),
        Signal("मृत्युपत्र", W_DISTINCTIVE),
        Signal("इच्छापत्र", W_DISTINCTIVE),
        Signal(r"last[\s\-_]*will", W_STRONG, regex=True),
        Signal("testator", W_STRONG),
        Signal("bequeath", W_STRONG),
        Signal("executor", W_SUPPORTING),
        Signal(r"\bwill\b", W_WEAK, regex=True),
    ),
    "7_12_extract": (
        Signal(
            rf"(?<![{_DIGITS}])[7\u096d]\s*[/\\\-.–—]\s*[1\u0967][2\u0968](?![{_DIGITS}])",
            W_DISTINCTIVE,
            regex=True,
        ),
        Signal(rf"(?<![{_DIGITS}])7_12(?![{_DIGITS}])", W_DISTINCTIVE, regex=True),
        Signal(rf"(?<![{_DIGITS}])7\s+12(?![{_DIGITS}])", W_DISTINCTIVE, regex=True),
        Signal("सातबारा", W_DISTINCTIVE),
        Signal(r"गाव[\s\-_]*नमुना[\s\-_]*सात", W_DISTINCTIVE, regex=True),
        Signal(r"अधिकार[\s\-_]*अभिलेख", W_DISTINCTIVE, regex=True),
        Signal("धारणा", W_STRONG),
        Signal(r"pik[\s\-_]*pratyakshik", W_STRONG, regex=True),
        Signal("पिक प्रत्यक्षिक", W_STRONG),
        # Survey numbers are frequently "712": kept under the floor alone so a
        # stray number in the text cannot classify, while "712.pdf" (2x) can.
        Signal(rf"(?<![{_DIGITS}])712(?![{_DIGITS}])", W_SUPPORTING, regex=True),
    ),
    "8a_record": (
        Signal(r"village[\s\-_]*form[\s\-_]*8[\s\-]*a", W_DISTINCTIVE, regex=True),
        Signal(r"नमुना[\s\-_]*आठ", W_DISTINCTIVE, regex=True),
        Signal(r"आठ[\s\-–—]*अ\b", W_DISTINCTIVE, regex=True),
        Signal(rf"(?<![{_DIGITS}])[8\u096e][\s\-]*[aअ]\b", W_STRONG, regex=True),
    ),
    "ferfar": (
        Signal("ferfar", W_DISTINCTIVE),
        Signal("फेरफार", W_DISTINCTIVE),
        Signal(r"फेरफार[\s\-_]*नोंद", W_DISTINCTIVE, regex=True),
        Signal(r"mutation[\s\-_]*entry", W_DISTINCTIVE, regex=True),
        Signal(r"\bmutation\b", W_SUPPORTING, regex=True),
    ),
    "property_card": (
        Signal(r"property[\s\-_]*card", W_DISTINCTIVE, regex=True),
        Signal(r"मालमत्ता[\s\-_]*पत्रक", W_DISTINCTIVE, regex=True),
        Signal(r"मालमत्ता[\s\-_]*कार्ड", W_DISTINCTIVE, regex=True),
        Signal("सिटी सर्व्हे", W_DISTINCTIVE),
        Signal("सिटी सर्वे", W_DISTINCTIVE),
        Signal(r"city[\s\-_]*survey", W_STRONG, regex=True),
        Signal(r"\bcts\b", W_SUPPORTING, regex=True),
        # Weak: "मालमत्ता" (property) appears in most land documents.
        Signal("मालमत्ता", W_WEAK),
    ),
    "ec": (
        Signal("encumbrance", W_DISTINCTIVE),
        Signal("encumbrance certificate", W_DISTINCTIVE),
        Signal("भारनियमिता", W_DISTINCTIVE),
        Signal(r"खरेदी[\s\-–—]*विक्री[\s\-–—]*भार", W_DISTINCTIVE, regex=True),
        Signal("encumbered", W_STRONG),
        Signal(r"\be[\s.]*c[\s.]*no\b", W_STRONG, regex=True),
        Signal(r"\bec\b", W_SUPPORTING, regex=True),
    ),
    "rera": (
        Signal(r"\brera\b", W_DISTINCTIVE, regex=True),
        Signal("महारेरा", W_DISTINCTIVE),
        Signal("रेरा", W_DISTINCTIVE),
        Signal(r"maha[\s\-_]*rera", W_DISTINCTIVE, regex=True),
        Signal(r"rera[\s\-_]*registration", W_DISTINCTIVE, regex=True),
        Signal(r"real[\s\-_]*estate[\s\-_]*regulatory", W_STRONG, regex=True),
    ),
    "court_document": (
        Signal("court", W_DISTINCTIVE),
        Signal(r"civil[\s\-_]*suit", W_DISTINCTIVE, regex=True),
        Signal("decree", W_DISTINCTIVE),
        Signal("न्यायालय", W_DISTINCTIVE),
        Signal("फैसला", W_DISTINCTIVE),
        Signal("दावा", W_STRONG),
        Signal("litigation", W_STRONG),
        Signal("judgment", W_STRONG),
        Signal("judgement", W_STRONG),
        Signal("आदेश", W_SUPPORTING),
        Signal("plaintiff", W_SUPPORTING),
        Signal("defendant", W_SUPPORTING),
        Signal("वादी", W_SUPPORTING),
        Signal("प्रतिवादी", W_SUPPORTING),
    ),
    "other": (),
    "unknown": (),
}

_TYPE_GAPS = set(PATTERNS) ^ KNOWN_DOC_TYPES
if _TYPE_GAPS - {"other", "unknown"}:
    raise ValueError(
        f"PATTERNS must cover app.models.enums.KNOWN_DOC_TYPES, gaps: {sorted(_TYPE_GAPS)}"
    )


@dataclass(frozen=True)
class _Matcher:
    """Pre-compiled :class:`Signal` ready to be run against a view string."""

    signal: Signal
    finder: re.Pattern[str] | str

    def hits(self, view: str) -> bool:
        if isinstance(self.finder, str):
            return self.finder in view
        return self.finder.search(view) is not None


def _compile(signal: Signal) -> _Matcher:
    if signal.regex:
        return _Matcher(signal, re.compile(signal.pattern, re.IGNORECASE | re.UNICODE))
    return _Matcher(signal, signal.pattern.casefold())


_MATCHERS: dict[str, tuple[_Matcher, ...]] = {
    doc_type: tuple(_compile(signal) for signal in signals)
    for doc_type, signals in PATTERNS.items()
}


def _normalize(value: str) -> str:
    """NFC + casefold, so matching is case- and composition-insensitive."""
    return unicodedata.normalize("NFC", value).casefold()


def _basename(filename: str) -> str:
    """Last path component, so upload folders cannot contribute signals."""
    return _PATH_SEPARATORS.split(filename or "")[-1]


def _views(value: str) -> tuple[str, ...]:
    """The as-is view plus a humanised view (``sale_deed`` -> ``sale deed``)."""
    raw = _normalize(value)
    humanised = _WORD_SEPARATORS.sub(" ", raw).strip()
    return (raw, humanised) if humanised != raw else (raw,)


def _channel_score(
    matchers: tuple[_Matcher, ...], views: tuple[str, ...]
) -> tuple[float, frozenset[str]]:
    """Weighted score plus the distinct signal patterns that matched any view."""
    score = 0.0
    matched: set[str] = set()
    for matcher in matchers:
        if any(matcher.hits(view) for view in views):
            matched.add(matcher.signal.pattern)
            score += matcher.signal.weight
    return score, frozenset(matched)


def _confidence(score: float) -> float:
    """Piecewise-linear ``_CONFIDENCE_CURVE`` lookup with clamping."""
    if score <= _CONFIDENCE_CURVE[0][0]:
        return _CONFIDENCE_CURVE[0][1]
    for (lo_score, lo_conf), (hi_score, hi_conf) in zip(_CONFIDENCE_CURVE, _CONFIDENCE_CURVE[1:]):
        if score <= hi_score:
            span = hi_score - lo_score
            ratio = 0.0 if span <= 0 else (score - lo_score) / span
            return lo_conf + (hi_conf - lo_conf) * ratio
    return _CONFIDENCE_CURVE[-1][1]


class KeywordDocClassifier:
    """Score-based keyword/regex classifier for Maharashtra property documents.

    Satisfies :class:`app.services.interfaces.DocClassifier`: ``classify``
    never raises for ``text=None``/empty text and always answers with a
    ``KNOWN_DOC_TYPES`` value (``"unknown"`` when the evidence is too weak).
    """

    engine_version: str = ENGINE_VERSION

    def classify(self, filename: str, text: str | None = None) -> ClassificationResult:
        name_views = _views(_basename(filename))
        text_views = _views(text) if text else ()

        scores: dict[str, float] = {}
        matched_signals: dict[str, frozenset[str]] = {}
        for doc_type, matchers in _MATCHERS.items():
            if not matchers:
                continue
            name_score, name_hits = _channel_score(matchers, name_views)
            text_score, text_hits = _channel_score(matchers, text_views)
            if name_score or text_score:
                scores[doc_type] = name_score * FILENAME_WEIGHT + text_score * TEXT_WEIGHT
                matched_signals[doc_type] = name_hits | text_hits

        if not scores:
            return self._unknown(NO_SIGNAL_CONFIDENCE)

        # Deterministic ranking: score, then breadth, then machine value.
        ranked = sorted(
            scores,
            key=lambda doc_type: (-scores[doc_type], -len(matched_signals[doc_type]), doc_type),
        )
        winner = ranked[0]
        top_score = scores[winner]
        if top_score < MIN_TOP_SCORE:
            return self._unknown(WEAK_ONLY_CONFIDENCE)

        runner_up = scores[ranked[1]] if len(ranked) > 1 else 0.0
        dominance = top_score / (top_score + runner_up)
        confidence = _confidence(top_score) * (
            DOMINANCE_FLOOR + (1.0 - DOMINANCE_FLOOR) * dominance
        )
        return ClassificationResult(
            doc_type=winner,
            confidence=round(min(max(confidence, 0.0), MAX_CONFIDENCE), 2),
            engine_version=self.engine_version,
        )

    @staticmethod
    def _unknown(confidence: float) -> ClassificationResult:
        return ClassificationResult(
            doc_type="unknown",
            confidence=confidence,
            engine_version=ENGINE_VERSION,
        )
