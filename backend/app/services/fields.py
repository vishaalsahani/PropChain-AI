"""Canonical extraction-field vocabulary (frozen in Phase 2).

Sources for the field list:
- FR-2 (Review-III slide 10): "names, dates, survey numbers, area and owner details".
- Specs p.2 Table 3 ("Entity Extraction"): "names, dates, survey/Gat/CTS numbers,
  ULPIN where available, area, boundaries, registration numbers, consideration/value
  references, parties, and document references."

The legacy ``documents.extracted_data`` blob keys (the eight names the pre-Phase-1
mock already exposed) stay a subset of this vocabulary so the API shape is stable:

    owner_name, seller_name, buyer_name, survey_number, gat_number, area_sqft,
    registration_date, registration_number

``area_sqft`` is a *derived* compatibility field: ``area`` + ``area_unit`` hold what
the document actually said and ``area_sqft`` carries the converted value when the
unit is known (conversion table in ``app.services.normalize``). Derived values are
never fabricated: an unknown unit means no ``area_sqft`` candidate.
"""

from __future__ import annotations

#: Fields extracted from documents (machine names, snake_case).
CANONICAL_FIELDS: tuple[str, ...] = (
    "owner_name",
    "seller_name",
    "buyer_name",
    "survey_number",
    "gat_number",
    "cts_number",
    "ulpin",
    "village",
    "taluka",
    "district",
    "area",
    "area_unit",
    "area_sqft",
    "registration_date",
    "execution_date",
    "registration_number",
    "consideration_amount",
    "currency",
    "boundaries",
    "referred_document",
)

#: Keys the pre-Phase-1 API blob always exposed (kept for frontend compatibility).
LEGACY_BLOB_KEYS: tuple[str, ...] = (
    "owner_name",
    "seller_name",
    "buyer_name",
    "survey_number",
    "gat_number",
    "area_sqft",
    "registration_date",
    "registration_number",
)

#: The four fields AC-2 measures ("owner, survey number, area, date").
HEADLINE_FIELDS: tuple[str, ...] = (
    "owner_name",
    "survey_number",
    "area_sqft",
    "registration_date",
)

#: value_type per field (free-form String(32) on ExtractedField; these are the
#: values the pipeline writes).
FIELD_VALUE_TYPES: dict[str, str] = {
    "owner_name": "string",
    "seller_name": "string",
    "buyer_name": "string",
    "survey_number": "identifier",
    "gat_number": "identifier",
    "cts_number": "identifier",
    "ulpin": "identifier",
    "village": "string",
    "taluka": "string",
    "district": "string",
    "area": "number",
    "area_unit": "string",
    "area_sqft": "number",
    "registration_date": "date",
    "execution_date": "date",
    "registration_number": "identifier",
    "consideration_amount": "number",
    "currency": "string",
    "boundaries": "string",
    "referred_document": "string",
}


def value_type_for(field_name: str) -> str:
    """value_type for a canonical field ('string' for anything unlisted)."""
    return FIELD_VALUE_TYPES.get(field_name, "string")
