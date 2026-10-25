"""Maharashtra due-diligence rule pack v1 (Phase 3, FR-5, AC-6).

``MaharashtraRuleEngine`` is the code-level fallback for the built-in
``mh-v1`` pack. The same rule definitions and evaluator are used by the
database-backed engine (``app.services.rule_store.DatabaseRuleEngine``), so a
fresh installation and an edited catalogue produce findings through one code
path.

Rules (id -> what triggers it):

===================  =======================================================
``MH-DOC-001``       no completed document extraction at all
``MH-LAND-712``      no 7/12 extract among the uploads
``MH-IDENT-001``     Maharashtra property profile without survey/Gat/CTS
``MH-IDENT-002``     profile identifier disagrees with an extracted one
``MH-CHAIN-001``     an ownership step whose transferor is not evidenced
``MH-CHAIN-002``     only an agreement to sale, no registered transfer
``MH-CHAIN-003``     no ownership evidence (no transfer, no holder record)
``MH-ENC-001``       a mortgage deed is among the documents
``MH-SUCC-001``      a will or partition deed needs succession review
``MH-LIT-001``       a court document is among the documents
``MH-AREA-001``      a document area deviates >5% from the profile area
``MH-INTEGRITY-001`` an uploaded document's hash is recorded as mismatched
===================  =======================================================

Every rule is a *screening indicator*, worded so a reviewer can verify it --
none of them declares fraud or an invalid title (Conflict-Handling rule,
master plan 1.4).
"""

from __future__ import annotations

from app.services.interfaces import FlagDraft
from app.services.rule_pack import BUILTIN_MH_RULES, evaluate_pack

#: Document area vs profile area mismatch tolerance (mirrors the v1 catalogue).
AREA_TOLERANCE = 0.05


class MaharashtraRuleEngine:
    """Code-level Maharashtra screening rules (v1 catalogue)."""

    engine_version = "mh-v1"

    def evaluate(self, property_profile: dict, extracted: list[dict]) -> list[FlagDraft]:
        return evaluate_pack(BUILTIN_MH_RULES, property_profile, extracted)
