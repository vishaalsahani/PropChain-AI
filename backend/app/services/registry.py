"""Engine registry: lazily constructed singletons selected via app config.

Selection reads (optional) settings attributes from ``app.config.settings``
without requiring them to exist — ``getattr(settings, "ocr_engine", "fake")``.

Engines are addressed as ``"package.module:ClassName"`` strings and imported on
first use, so selecting the fake engines never imports the OCR/NLP heavyweights
(pytesseract, OpenCV) and a machine without Tesseract can still boot. An unknown
engine *name* logs a warning and falls back to the fake implementation (a typo
cannot brick the app); a known name whose module fails to import raises at first
use — loud failure beats silently serving mock data.

Usage:
    from app.services.registry import get_rule_engine
    flags = get_rule_engine().evaluate(property_profile, extracted)
"""

from __future__ import annotations

import importlib
import logging
from threading import Lock
from typing import Any, cast

from app.config import settings
from app.services.interfaces import (
    CrossValidator,
    DocClassifier,
    NLPExtractor,
    OcrService,
    OwnershipGraphBuilder,
    RuleEngine,
)

logger = logging.getLogger(__name__)

DEFAULT_ENGINE = "fake"

#: component key -> (settings attribute name, engine name -> "module:Class")
_COMPONENTS: dict[str, tuple[str, dict[str, str]]] = {
    "ocr": (
        "ocr_engine",
        {
            "fake": "app.services.fakes:FakeOcrService",
            "tesseract": "app.services.ocr_tesseract:TesseractOcrService",
        },
    ),
    "classifier": (
        "doc_classifier_engine",
        {
            "fake": "app.services.fakes:FakeDocClassifier",
            "keyword": "app.services.classifier_keyword:KeywordDocClassifier",
        },
    ),
    "nlp": (
        "nlp_extractor_engine",
        {
            "fake": "app.services.fakes:FakeNLPExtractor",
            "patterns": "app.services.nlp_patterns:PatternNLPExtractor",
        },
    ),
    "cross_validator": (
        "cross_validator_engine",
        {
            "fake": "app.services.fakes:FakeCrossValidator",
            "matrix": "app.services.cross_validate:MatrixCrossValidator",
        },
    ),
    "ownership_builder": (
        "ownership_builder_engine",
        {
            "fake": "app.services.fakes:FakeOwnershipGraphBuilder",
            "evidence": "app.services.ownership_evidence:EvidenceOwnershipBuilder",
        },
    ),
    "rule_engine": (
        "rule_engine",
        {
            "fake": "app.services.fakes:FakeRuleEngine",
            "mh_pack": "app.services.rules_mh:MaharashtraRuleEngine",
        },
    ),
}

_CACHE: dict[str, Any] = {}
_LOCK = Lock()


def _engine_choice(settings_name: str, default: str = DEFAULT_ENGINE) -> str:
    """Read the configured engine name for one component (never raises)."""
    value = getattr(settings, settings_name, default)
    if value is None:
        return default
    choice = str(value).strip().lower()
    return choice or default


def _resolve_class(dotted: str) -> type:
    """Import ``"app.services.x:ClassName"`` on demand."""
    module_name, _, class_name = dotted.partition(":")
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _get_engine(component: str) -> Any:
    cached = _CACHE.get(component)
    if cached is not None:
        return cached

    with _LOCK:
        cached = _CACHE.get(component)
        if cached is not None:
            return cached

        settings_name, engines = _COMPONENTS[component]
        choice = _engine_choice(settings_name)
        dotted = engines.get(choice)
        if dotted is None:
            logger.warning(
                "Engine %r configured via settings.%s is not implemented; using 'fake'",
                choice,
                settings_name,
            )
            dotted = engines[DEFAULT_ENGINE]

        engine = _resolve_class(dotted)()
        _CACHE[component] = engine
        return engine


def reset_engine_cache() -> None:
    """Drop the cached singletons (used by tests that patch settings)."""
    with _LOCK:
        _CACHE.clear()


def get_ocr_service() -> OcrService:
    return cast(OcrService, _get_engine("ocr"))


def get_doc_classifier() -> DocClassifier:
    return cast(DocClassifier, _get_engine("classifier"))


def get_nlp_extractor() -> NLPExtractor:
    return cast(NLPExtractor, _get_engine("nlp"))


def get_cross_validator() -> CrossValidator:
    return cast(CrossValidator, _get_engine("cross_validator"))


def get_ownership_builder() -> OwnershipGraphBuilder:
    return cast(OwnershipGraphBuilder, _get_engine("ownership_builder"))


def get_rule_engine() -> RuleEngine:
    return cast(RuleEngine, _get_engine("rule_engine"))
