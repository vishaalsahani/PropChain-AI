"""Evidence-based ownership chain construction (Phase 3, FR-7, AC-5).

``EvidenceOwnershipBuilder`` reads the *extracted* fields of every completed
document and derives the property's transfer history from what the documents
actually state:

* ``sale_deed`` / ``gift_deed`` / ``partition_deed`` / ``agreement_to_sale``
  describe a transfer (agreement is kept as ``agreement`` — it is not a
  completed conveyance);
* a ``ferfar`` mutation corroborates the deed it references (matched by
  registration number); a mutation whose deed was not uploaded becomes its own
  step with an unknown transferor and ``gap_flag=True``;
* land records (7/12, 8A, property card, EC) and wills are *records*, not
  transfers: they never create chain steps, but they are the fallback evidence
  for "current holder" when no transfer has been uploaded;
* mortgage deeds are charges against the property, not ownership changes, so
  they stay out of the chain (the rule engine raises them instead).

Linking: events are ordered by date (registration date, else execution date;
undated events keep document order and sort last), then each step's transferor
is matched against the previous step's transferee with the shared fuzzy name
comparison (≥85). ``gap_flag`` is set when the transferor of a step cannot be
evidenced by an earlier uploaded document, or when a referenced predecessor
instrument is not among the uploads — this is the "gap" AC-5 asks to surface.
"""

from __future__ import annotations

from typing import Any

from app.services import normalize
from app.services.interfaces import OwnershipDraft

#: Fuzzy-match threshold linking one step's seller to the previous step's buyer.
CHAIN_LINK_THRESHOLD = 85.0

#: Document types that describe a transfer, with the resulting transfer_type.
_TRANSFER_TYPES = {
    "sale_deed": "sale",
    "gift_deed": "gift",
    "partition_deed": "partition",
    "agreement_to_sale": "agreement",
}

#: Document types that merely record the current holder of the property.
_RECORD_TYPES = ("7_12_extract", "8a_record", "property_card", "ec")


class _Event:
    """One candidate transfer step, before ordering and linking."""

    __slots__ = ("doc_id", "filename", "doc_type", "transfer_type",
                 "from_party", "to_party", "date", "registration",
                 "referred", "corroboration")

    def __init__(
        self,
        doc_id: int,
        filename: str,
        doc_type: str,
        transfer_type: str,
        from_party: str | None,
        to_party: str,
        date: str | None,
        registration: str | None,
        referred: str | None,
        corroboration: str | None = None,
    ):
        self.doc_id = doc_id
        self.filename = filename
        self.doc_type = doc_type
        self.transfer_type = transfer_type
        self.from_party = from_party
        self.to_party = to_party
        self.date = date
        self.registration = registration
        self.referred = referred
        self.corroboration = corroboration

    def ref(self) -> str:
        label = self.filename
        if self.corroboration:
            label = f"{label}; mutation: {self.corroboration}"
        return label


class EvidenceOwnershipBuilder:
    """Builds the ownership chain from extracted document evidence."""

    engine_version = "evidence-v1"

    def build(self, document_meta: dict[int, dict]) -> list[OwnershipDraft]:
        documents = _documents(document_meta)
        events = _transfer_events(documents)
        if not events:
            return _record_fallback(documents)
        return _link_chain(_order_events(events), documents)


class _Doc:
    __slots__ = ("doc_id", "filename", "doc_type", "payload")

    def __init__(self, doc_id: int, meta: dict[str, Any]):
        self.doc_id = doc_id
        self.filename = str(meta.get("filename") or f"document {doc_id}")
        self.doc_type = str(meta.get("doc_type") or "unknown")
        extracted = meta.get("extracted")
        self.payload: dict[str, Any] = extracted if isinstance(extracted, dict) else {}

    def get(self, field: str) -> str | None:
        value = self.payload.get(field)
        if value is None:
            return None
        text = normalize.normalize_whitespace(str(value))
        return text or None

    def iso_date(self) -> str | None:
        for field in ("registration_date", "execution_date"):
            raw = self.get(field)
            if raw:
                parsed = normalize.parse_iso_date(raw)
                if parsed:
                    return parsed
        return None


def _documents(document_meta: dict[int, dict]) -> list[_Doc]:
    return [_Doc(doc_id, document_meta[doc_id] or {}) for doc_id in sorted(document_meta)]


def _transfer_events(documents: list[_Doc]) -> list[_Event]:
    """One event per transfer document, with matching ferfar corroboration."""
    events: list[_Event] = []
    by_registration: dict[str, _Event] = {}

    for doc in documents:
        transfer_type = _TRANSFER_TYPES.get(doc.doc_type)
        if transfer_type is None:
            continue
        to_party = doc.get("buyer_name") or doc.get("owner_name")
        from_party = doc.get("seller_name")
        if not to_party:
            continue  # nothing to show as a chain step
        event = _Event(
            doc_id=doc.doc_id,
            filename=doc.filename,
            doc_type=doc.doc_type,
            transfer_type=transfer_type,
            from_party=from_party,
            to_party=to_party,
            date=doc.iso_date(),
            registration=doc.get("registration_number"),
            referred=doc.get("referred_document"),
        )
        events.append(event)
        key = normalize.normalize_registration_number(event.registration or "")
        if key:
            by_registration[key] = event

    for doc in documents:
        if doc.doc_type != "ferfar":
            continue
        owner = doc.get("owner_name")
        if not owner:
            continue
        key = normalize.normalize_registration_number(doc.get("registration_number") or "")
        corroborated = by_registration.get(key) if key else None
        if corroborated is not None:
            corroborated.corroboration = doc.filename
            # The mutation date is when the transfer took effect; prefer it.
            mutation_date = doc.iso_date()
            if mutation_date:
                corroborated.date = mutation_date
            continue
        events.append(
            _Event(
                doc_id=doc.doc_id,
                filename=doc.filename,
                doc_type=doc.doc_type,
                transfer_type="mutation",
                from_party=None,
                to_party=owner,
                date=doc.iso_date(),
                registration=doc.get("registration_number"),
                referred=doc.get("referred_document"),
            )
        )
    return events


def _order_events(events: list[_Event]) -> list[_Event]:
    """Chronological order; undated events keep document order and sort last."""
    return sorted(
        events,
        key=lambda event: (event.date is None, event.date or "", event.doc_id),
    )


def _link_chain(events: list[_Event], documents: list[_Doc]) -> list[OwnershipDraft]:
    drafts: list[OwnershipDraft] = []

    for index, event in enumerate(events):
        gap = False
        if event.from_party is None:
            # Mutation without the underlying deed, or a record without a
            # transferor: the previous link is unknown.
            gap = True
        elif index == 0:
            # The earliest uploaded transfer is the *root* of the traced chain —
            # it is not a gap by itself. It becomes one when it points at a
            # predecessor instrument that was not uploaded.
            gap = bool(event.referred) and not _referenced_uploaded(
                event.referred, documents, event
            )
        else:
            previous = events[index - 1]
            gap = normalize.name_similarity(previous.to_party, event.from_party) < CHAIN_LINK_THRESHOLD

        drafts.append(
            OwnershipDraft(
                from_party=event.from_party,
                to_party=event.to_party,
                transfer_type=event.transfer_type,
                transfer_date=event.date,
                document_ref=event.ref(),
                sequence=index + 1,
                gap_flag=gap,
            )
        )
    return drafts


def _referenced_uploaded(referred: str, documents: list[_Doc], event: _Event) -> bool:
    """True when the referenced predecessor instrument is one of the uploads.

    Only a document's *own* registration number can satisfy the reference: an
    uploaded record that merely cites the same predecessor (an EC or another
    deed repeating the number in its own ``referred_document`` field) is not
    that predecessor, so it must not close the gap.
    """
    needle = normalize.normalize_registration_number(referred)
    if not needle or len(needle) < 4:
        return False
    for doc in documents:
        if doc.doc_id == event.doc_id:
            continue
        haystack = normalize.normalize_registration_number(doc.get("registration_number") or "")
        if haystack and (needle in haystack or haystack in needle):
            return True
    return False


def _record_fallback(documents: list[_Doc]) -> list[OwnershipDraft]:
    """No transfers uploaded: show the recorded holder rather than nothing."""
    for doc in documents:
        if doc.doc_type not in _RECORD_TYPES:
            continue
        holder = doc.get("owner_name")
        if holder:
            return [
                OwnershipDraft(
                    from_party=None,
                    to_party=holder,
                    transfer_type="record",
                    transfer_date=None,
                    document_ref=doc.filename,
                    sequence=1,
                    gap_flag=False,
                )
            ]
    return []
