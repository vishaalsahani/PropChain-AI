"""Unit tests for ``app.services.ownership_evidence.EvidenceOwnershipBuilder`` (Phase 3).

Standalone by design: no conftest fixtures, no app boot, no DB, no OCR — the
engine is a pure function over the metadata the pipeline assembles for one
property, ``{doc_id: {"filename", "doc_type", "extracted": {...}}}``. The field
values below mirror what ``scripts/make_fixtures.py`` prints and
``PatternNLPExtractor`` reads back (same labels, English spellings), so a green
run means the engine works on real extraction output rather than toy strings.
"""

from __future__ import annotations

from datetime import date

from app.services.interfaces import OwnershipDraft, OwnershipGraphBuilder
from app.services.ownership_evidence import EvidenceOwnershipBuilder

#: Reported by the builder; pinned here so a silent engine bump fails loudly.
ENGINE_VERSION = "evidence-v1"


# --------------------------------------------------------------------------
# Helpers: document metadata in the pipeline's shape
# --------------------------------------------------------------------------


def doc(filename: str, doc_type: str, **fields: str) -> dict:
    """One ``document_meta`` entry: filename, classifier output, extracted fields."""
    return {"filename": filename, "doc_type": doc_type, "extracted": dict(fields)}


def with_referral(entry: dict, referred_document: str) -> dict:
    """The same entry with its ``referred_document`` field filled in."""
    return {
        **entry,
        "extracted": {**entry["extracted"], "referred_document": referred_document},
    }


def meta(*entries: dict) -> dict[int, dict]:
    """``document_meta`` keyed by 1-based document ids, in upload order."""
    return dict(enumerate(entries, start=1))


def chain(document_meta: dict[int, dict]) -> list[OwnershipDraft]:
    """Build the ownership chain for one property's document metadata."""
    return EvidenceOwnershipBuilder().build(document_meta)


#: 1998 predecessor deed — the root of the traced chain; refers to nothing else.
SALE_1998 = doc(
    "sale_deed_1998.pdf",
    "sale_deed",
    seller_name="Dagdu Shinde",
    buyer_name="Vithal More",
    survey_number="124/A",
    registration_number="MH-PUN-1998-44556",
    registration_date="12/05/1998",
)

#: 2009 deed carrying the chain forward to Shantaram Pawar.
SALE_2009 = doc(
    "sale_deed_2009.pdf",
    "sale_deed",
    seller_name="Vithal More",
    buyer_name="Shantaram Pawar",
    survey_number="124/A",
    registration_number="MH-PUN-2009-88123",
    registration_date="15/06/2009",
)


# --------------------------------------------------------------------------
# Engine contract
# --------------------------------------------------------------------------


def test_engine_version_is_reported():
    builder = EvidenceOwnershipBuilder()
    assert builder.engine_version == EvidenceOwnershipBuilder.engine_version == ENGINE_VERSION
    assert EvidenceOwnershipBuilder.engine_version == "evidence-v1"


def test_satisfies_ownership_graph_builder_protocol():
    builder = EvidenceOwnershipBuilder()
    assert isinstance(builder, OwnershipGraphBuilder)
    assert isinstance(builder.engine_version, str)


# --------------------------------------------------------------------------
# Chain construction: ordering, sequences, linking
# --------------------------------------------------------------------------


def test_two_deed_chain_links_without_gaps():
    """Dagdu -> Vithal (1998) then Vithal -> Shantaram (2009), oldest first.

    The 2009 deed refers to a predecessor instrument that is *not* among the
    uploads, yet the step is evidenced: its seller is the previous step's buyer.
    """
    document_meta = meta(
        SALE_1998,
        with_referral(SALE_2009, "Predecessor Sale Deed No. MH-PUN-1990-11111"),
    )
    drafts = chain(document_meta)

    assert len(drafts) == 2
    assert all(isinstance(draft, OwnershipDraft) for draft in drafts)
    assert [draft.sequence for draft in drafts] == [1, 2]
    assert [draft.gap_flag for draft in drafts] == [False, False]
    assert [draft.transfer_type for draft in drafts] == ["sale", "sale"]
    assert [(draft.from_party, draft.to_party) for draft in drafts] == [
        ("Dagdu Shinde", "Vithal More"),
        ("Vithal More", "Shantaram Pawar"),
    ]
    assert [draft.document_ref for draft in drafts] == [
        "sale_deed_1998.pdf",
        "sale_deed_2009.pdf",
    ]

    first_date, second_date = (draft.transfer_date for draft in drafts)
    assert first_date == "1998-05-12"
    assert second_date == "2009-06-15"
    # ISO strings that also compare chronologically as written.
    assert date.fromisoformat(first_date) < date.fromisoformat(second_date)


def test_middle_link_gap_when_the_seller_is_unrelated():
    """A 1998 deed cannot evidence a 2015 deed sold by a different family."""
    document_meta = meta(
        SALE_1998,
        doc(
            "sale_deed_2015.pdf",
            "sale_deed",
            seller_name="Baban Kale",
            buyer_name="Shantaram Pawar",
            registration_number="MH-PUN-2015-31313",
            registration_date="20/01/2015",
        ),
    )
    first, second = chain(document_meta)

    assert first.gap_flag is False
    assert (first.from_party, first.to_party) == ("Dagdu Shinde", "Vithal More")
    assert second.from_party == "Baban Kale"
    assert second.gap_flag is True
    assert [first.sequence, second.sequence] == [1, 2]


def test_undated_transfer_sorts_last_with_contiguous_sequences():
    """Date order wins over upload order; an undated deed never opens the chain."""
    document_meta = meta(
        doc(
            "sale_deed_undated.pdf",
            "sale_deed",
            seller_name="Shantaram Pawar",
            buyer_name="Prakash Jagtap",
        ),
        SALE_2009,
    )
    drafts = chain(document_meta)

    assert [draft.document_ref for draft in drafts] == [
        "sale_deed_2009.pdf",
        "sale_deed_undated.pdf",
    ]
    assert [draft.sequence for draft in drafts] == [1, 2]
    assert drafts[0].transfer_date == "2009-06-15"
    assert drafts[1].transfer_date is None
    assert [draft.gap_flag for draft in drafts] == [False, False]


def test_impossible_registration_date_is_treated_as_undated():
    """31/02/2011 does not exist: the date stays empty instead of being guessed."""
    document_meta = meta(
        SALE_2009,
        doc(
            "sale_deed_bad_date.pdf",
            "sale_deed",
            seller_name="Shantaram Pawar",
            buyer_name="Prakash Jagtap",
            registration_date="31/02/2011",
        ),
    )
    drafts = chain(document_meta)

    assert [draft.document_ref for draft in drafts] == [
        "sale_deed_2009.pdf",
        "sale_deed_bad_date.pdf",
    ]
    assert [draft.sequence for draft in drafts] == [1, 2]
    assert drafts[1].transfer_date is None
    assert drafts[1].from_party == "Shantaram Pawar"  # still linked by name


# --------------------------------------------------------------------------
# Root-of-chain referrals (AC-5 gaps)
# --------------------------------------------------------------------------


def test_root_step_is_a_gap_when_the_referred_deed_was_not_uploaded():
    # Case A: the referred predecessor is the only thing missing from the case.
    [only_step] = chain(
        meta(with_referral(SALE_2009, "Predecessor Sale Deed No. MH-PUN-1990-11111"))
    )
    assert only_step.sequence == 1
    assert only_step.document_ref == "sale_deed_2009.pdf"
    assert only_step.gap_flag is True

    # Case B: the trace stops at the oldest upload, which itself refers to a 1990
    # deed nobody uploaded — the gap belongs to the root, not to the 2009 link.
    drafts = chain(
        meta(
            with_referral(SALE_1998, "Predecessor Sale Deed No. MH-PUN-1990-11111"),
            SALE_2009,
        )
    )
    assert [draft.gap_flag for draft in drafts] == [True, False]


def test_root_step_is_not_a_gap_when_the_referred_deed_is_uploaded():
    """A referred predecessor found among the uploads closes the root gap.

    Only the seller name and the registration block of the 1998 scan were
    extracted (a realistic partial extraction), so that deed adds no step of its
    own — but it *is* among the uploads, which is what the check looks at.
    """
    document_meta = meta(
        with_referral(SALE_2009, "Predecessor Sale Deed No. MH-PUN-1998-44556"),
        doc(
            "sale_deed_1998_partial.pdf",
            "sale_deed",
            seller_name="Dagdu Shinde",
            registration_number="MH-PUN-1998-44556",
            registration_date="12/05/1998",
        ),
    )
    [draft] = chain(document_meta)

    assert draft.sequence == 1
    assert draft.document_ref == "sale_deed_2009.pdf"
    assert draft.gap_flag is False


def test_citing_record_does_not_close_a_root_gap():
    """An upload that merely *cites* the missing deed is not that deed.

    Real ECs and deeds repeat the predecessor's number in their own
    ``referred_document`` field; only a document whose own registration number
    matches can satisfy the reference.
    """
    document_meta = meta(
        with_referral(SALE_2009, "Predecessor Sale Deed No. MH-PUN-1990-11111"),
        with_referral(
            doc("ec_2024.pdf", "ec", owner_name="Shantaram Pawar"),
            "Sale Deed No. MH-PUN-1990-11111",
        ),
    )
    [draft] = chain(document_meta)

    assert draft.document_ref == "sale_deed_2009.pdf"
    assert draft.gap_flag is True


# --------------------------------------------------------------------------
# Ferfar (mutation) corroboration
# --------------------------------------------------------------------------


def test_ferfar_merges_into_the_deed_it_corroborates():
    """Same registration number => one step, with the mutation as its evidence."""
    ferfar = doc(
        "ferfar_2009.pdf",
        "ferfar",
        owner_name="Shantaram Pawar",
        registration_number="MH-PUN-2009-88123",
        registration_date="20/07/2009",
    )
    [draft] = chain(meta(SALE_2009, ferfar))  # exactly one step: merged, not added

    assert draft.transfer_type == "sale"
    assert draft.sequence == 1
    assert draft.gap_flag is False
    assert draft.to_party == "Shantaram Pawar"
    assert draft.document_ref.startswith("sale_deed_2009.pdf")
    assert "ferfar_2009.pdf" in draft.document_ref
    # The mutation date is when the transfer took effect, so it wins.
    assert draft.transfer_date == "2009-07-20"


def test_ferfar_matching_ignores_registration_number_case():
    document_meta = meta(
        SALE_2009,
        doc(
            "ferfar_2009.pdf",
            "ferfar",
            owner_name="Shantaram Pawar",
            registration_number="mh-pun-2009-88123",
            registration_date="20/07/2009",
        ),
    )
    [draft] = chain(document_meta)  # merged, not a second step

    assert "sale_deed_2009.pdf" in draft.document_ref
    assert "ferfar_2009.pdf" in draft.document_ref
    assert draft.transfer_date == "2009-07-20"


def test_ferfar_without_its_deed_becomes_a_mutation_step():
    """An unmatched mutation is still shown, with an unknown transferor and a gap."""
    document_meta = meta(
        SALE_2009,
        doc(
            "ferfar_2011.pdf",
            "ferfar",
            owner_name="Shantaram Pawar",
            registration_number="MH-PUN-2011-77000",
            registration_date="10/10/2011",
        ),
    )
    sale_step, mutation = chain(document_meta)

    assert (sale_step.transfer_type, sale_step.gap_flag) == ("sale", False)

    assert mutation.transfer_type == "mutation"
    assert mutation.from_party is None
    assert mutation.to_party == "Shantaram Pawar"
    assert mutation.gap_flag is True
    assert mutation.sequence == 2
    assert mutation.document_ref == "ferfar_2011.pdf"
    assert mutation.transfer_date == "2011-10-10"


# --------------------------------------------------------------------------
# Records, charges and empty cases
# --------------------------------------------------------------------------


def test_record_fallback_uses_the_7_12_holder():
    """No transfer uploaded: the recorded holder is shown as a "record" step."""
    document_meta = meta(
        doc(
            "7_12_extract_2024.pdf",
            "7_12_extract",
            owner_name="Shantaram Pawar",
            survey_number="124/A",
            village="Wagholi",
        )
    )
    [draft] = chain(document_meta)

    assert draft == OwnershipDraft(
        from_party=None,
        to_party="Shantaram Pawar",
        transfer_type="record",
        transfer_date=None,
        document_ref="7_12_extract_2024.pdf",
        sequence=1,
        gap_flag=False,
    )


def test_mortgage_is_a_charge_not_a_chain_step():
    """A mortgage changes no ownership, so a mortgage-only case has no chain."""
    mortgage = doc(
        "mortgage_deed_2015.pdf",
        "mortgage_deed",
        seller_name="Shantaram Pawar",
        buyer_name="Pune District Co-op Bank",
        registration_number="MH-PUN-2015-60606",
        registration_date="01/04/2015",
    )
    assert chain(meta(mortgage)) == []
    # A recorded holder on the mortgage must not turn it into a record fallback.
    assert chain(meta({**mortgage, "extracted": {**mortgage["extracted"], "owner_name": "Shantaram Pawar"}})) == []


def test_records_and_wills_next_to_a_deed_add_no_steps():
    """7/12, 8A, property card, EC, will and mortgage are evidence, not steps."""
    document_meta = meta(
        SALE_1998,
        SALE_2009,
        doc("7_12_extract_2024.pdf", "7_12_extract", owner_name="Shantaram Pawar"),
        doc("8a_record_2024.pdf", "8a_record", owner_name="Shantaram Pawar"),
        doc("property_card_2020.pdf", "property_card", owner_name="Shantaram Pawar"),
        doc("ec_2024.pdf", "ec", owner_name="Shantaram Pawar", registration_number="MH-PUN-2024-12121"),
        doc("will_2010.pdf", "will", owner_name="Vithal More"),
        doc(
            "mortgage_deed_2012.pdf",
            "mortgage_deed",
            seller_name="Shantaram Pawar",
            buyer_name="Pune District Co-op Bank",
            registration_date="01/04/2012",
        ),
    )
    drafts = chain(document_meta)

    assert [(draft.sequence, draft.document_ref) for draft in drafts] == [
        (1, "sale_deed_1998.pdf"),
        (2, "sale_deed_2009.pdf"),
    ]


def test_empty_or_extractionless_meta_builds_no_chain():
    assert chain({}) == []
    assert chain(meta()) == []
    assert chain(meta(doc("sale_deed_2020.pdf", "sale_deed"))) == []
    assert chain(meta(doc("7_12_extract_2024.pdf", "7_12_extract"))) == []
    # Entries the pipeline could not fill: no "extracted" key, None, or empty.
    assert chain(meta({"filename": "scan_001.pdf", "doc_type": "sale_deed"})) == []
    assert chain(meta({"filename": "scan_002.pdf", "doc_type": "7_12_extract", "extracted": None})) == []
    assert chain({1: None, 2: {}}) == []


# --------------------------------------------------------------------------
# Transfer vocabulary
# --------------------------------------------------------------------------


def test_agreement_to_sale_is_not_a_completed_conveyance():
    document_meta = meta(
        doc(
            "agreement_to_sale_2009.pdf",
            "agreement_to_sale",
            seller_name="Vithal More",
            buyer_name="Shantaram Pawar",
            execution_date="02/03/2009",
        )
    )
    [draft] = chain(document_meta)

    assert draft.transfer_type == "agreement"
    assert draft.transfer_type != "sale"
    # Agreements are often unregistered: the execution date carries the step.
    assert draft.transfer_date == "2009-03-02"


def test_gift_deed_transfers_to_the_buyer_or_the_recorded_owner():
    gift = doc(
        "gift_deed_2010.pdf",
        "gift_deed",
        seller_name="Vithal More",  # the donor
        buyer_name="Shantaram Pawar",  # the donee
        registration_number="MH-PUN-2010-22222",
        registration_date="05/05/2010",
    )
    [draft] = chain(meta(gift))
    assert draft.transfer_type == "gift"
    assert (draft.from_party, draft.to_party) == ("Vithal More", "Shantaram Pawar")

    # Extractions that only caught the holder ("owner_name") still name the donee.
    owner_only = doc(
        "gift_deed_2010.pdf",
        "gift_deed",
        seller_name="Vithal More",
        owner_name="Shantaram Pawar",
        registration_date="05/05/2010",
    )
    [draft] = chain(meta(owner_only))
    assert draft.transfer_type == "gift"
    assert (draft.from_party, draft.to_party) == ("Vithal More", "Shantaram Pawar")
