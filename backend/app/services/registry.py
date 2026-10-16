"""Engine registry: lazily constructed singletons selected via app config.

Selection reads (optional) settings attributes from ``app.config.settings``
without requiring them to exist — ``getattr(settings, "ocr_engine", "fake")``.
Only the "fake" engines exist today, so any other value logs a warning and
falls back to the fake implementation instead of breaking the app.

Usage:
    from app.services.registry import get_rule_engine
    flags = get_rule_engine().evaluate(property_profile, extracted)
"""

from __future__ import annotations

import logging
from threading import Lock
from typing import Any, cast

from app.config import settings
from app.services import fakes
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

#: component key -> (settings attribute name, implemented engines by config value)
_COMPONENTS: dict[str, tuple[str, dict[str, type]]] = {
    "ocr": ("ocr_engine", {"fake": fakes.FakeOcrService}),
    "classifier": ("doc_classifier_engine", {"fake": fakes.FakeDocClassifier}),
    "nlp": ("nlp_extractor_engine", {"fake": fakes.FakeNLPExtractor}),
    "cross_validator": ("cross_validator_engine", {"fake": fakes.FakeCrossValidator}),
    "ownership_builder": ("ownership_builder_engine", {"fake": fakes.FakeOwnershipGraphBuilder}),
    "rule_engine": ("rule_engine", {"fake": fakes.FakeRuleEngine}),
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
        engine_cls = engines.get(choice)
        if engine_cls is None:
            logger.warning(
                "Engine %r configured via settings.%s is not implemented; using 'fake'",
                choice,
                settings_name,
            )
            engine_cls = engines[DEFAULT_ENGINE]

        engine = engine_cls()
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
