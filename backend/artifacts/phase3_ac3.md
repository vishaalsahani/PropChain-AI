# Phase 3 — AC-3 seeded-error detection report

- Generated: 2026-10-17 07:01 UTC
- Cases: `C:\Users\visha\AppData\Local\Temp\propchain_errorset` (21 cases, 24 findings total)
- Engines: ocr=`tesseract-5.5.3`, classifier=`keyword-v1`, nlp=`patterns-v1`, validator=`matrix-v1`, ownership=`evidence-v1`, rules=`mh-v1`

## Headline

- AC-3 seeded-error detection: **19/19 (100.0%)** (target ≥90%)
- Control cases without a seeded error: 2/2 (100.0%) clean (any finding would be a false positive)
- Verdict matching the expectation where pinned: 6/6 (100.0%)

## By error family

| family | cases | detected |
|---|---|---|
| Cross-document (matrix) | 9 | 9/9 (100.0%) |
| Ownership chain | 4 | 4/4 (100.0%) |
| Rule pack (charge/succession/litigation/land/identity/integrity) | 6 | 6/6 (100.0%) |

## Per case

### ✅ `control_clean`

- Seeded error: nothing: internally consistent control (english)
- Expected: — (control); observed: —
- Verdict: `verified` (expected `verified`)
  - reason: No ownership, identity, area, encumbrance or document-integrity findings were raised by the automated checks.
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]

### ✅ `survey_mismatch`

- Seeded error: 7/12 extract prints survey number 221/3 (english)
- Expected: `MATCH-SURVEY-001`; observed: `MATCH-SURVEY-001`, `MH-IDENT-002`
- Verdict: `flagged`
  - reason: High: Survey Number mismatch across documents (MATCH-SURVEY-001)
  - reason: High: Profile survey number differs from documents (MH-IDENT-002)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MATCH-SURVEY-001` (high, conf 0.85): Survey Number mismatch across documents — 221/2 in predecessor_sale_deed_1998.pdf (sale_deed), sale_deed_2009.pdf (sale_deed), ferfar_2009.pdf (ferfar), encumbrance_certificate_2024.pdf (ec), property_card_2024.pdf (property_card); 221/3 in 7_12_extract_2024.pdf (7_12_extract)
- Finding `MH-IDENT-002` (high, conf 0.85): Profile survey number differs from documents — Profile: 221/2; extracted: 221/3 in 7_12_extract_2024.pdf

### ✅ `owner_mismatch`

- Seeded error: 7/12 extract names a different holder (Baban Kale) (english)
- Expected: `MATCH-OWNER-001`; observed: `MATCH-OWNER-001`
- Verdict: `flagged`
  - reason: High: Owner name mismatch across documents (MATCH-OWNER-001)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MATCH-OWNER-001` (high, conf 0.8): Owner name mismatch across documents — Shantaram Pawar in ferfar_2009.pdf (ferfar), encumbrance_certificate_2024.pdf (ec), property_card_2024.pdf (property_card); Baban Kale in 7_12_extract_2024.pdf (7_12_extract)

### ✅ `area_drift`

- Seeded error: 2009 sale deed prints 2400 sq ft instead of 2000 (english)
- Expected: `MATCH-AREA-001`; observed: `MATCH-AREA-001`, `MH-AREA-001`
- Verdict: `needs_review`
  - reason: Medium: Area discrepancy detected (MATCH-AREA-001)
  - reason: Medium: Document area differs from the property profile (MH-AREA-001)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MATCH-AREA-001` (medium, conf 0.8): Area discrepancy detected — 1999.93262 sqft (sqm as printed) in property_card_2024.pdf (property_card); 2000 sqft (sqft as printed) in predecessor_sale_deed_1998.pdf (sale_deed); 2000 sqft (sqft as printed) in ferfar_2009.pdf (ferfar); 2000 sqft (sqft as printed) in 7_12_extract_2024.pdf (7_12_extract); 2000 sqft (sqft as printed) in encumbrance_certificate_2024.pdf (ec); 2400 sqft (sqft as printed) in sale_deed_2009.pdf (sale_deed)
- Finding `MH-AREA-001` (medium, conf 0.75): Document area differs from the property profile — Profile: 2000 sqft; documents: 2400 sqft (17% off)

### ✅ `boundary_change`

- Seeded error: property card describes different boundaries (english)
- Expected: `MATCH-BOUNDARY-001`; observed: `MATCH-BOUNDARY-001`
- Verdict: `needs_review`
  - reason: Medium: Boundary description mismatch (MATCH-BOUNDARY-001)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MATCH-BOUNDARY-001` (medium, conf 0.65): Boundary description mismatch — predecessor_sale_deed_1998.pdf (sale_deed) says "East: 30 ft DP road"; property_card_2024.pdf (property_card) says "East: canal" | sale_deed_2009.pdf (sale_deed) says "East: 30 ft DP road"; property_card_2024.pdf (property_card) says "East: canal"

### ✅ `duplicate_registration_number`

- Seeded error: 1998 deed reuses the 2009 registration number (english)
- Expected: `MATCH-REGNO-001`; observed: `MATCH-REGNO-001`
- Verdict: `needs_review`
  - reason: Medium: Registration number reused across documents (MATCH-REGNO-001)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MATCH-REGNO-001` (medium, conf 0.75): Registration number reused across documents — MH-PUN-2009-11223 appears in predecessor_sale_deed_1998.pdf (sale_deed), sale_deed_2009.pdf (sale_deed)

### ✅ `date_inversion`

- Seeded error: 2009 deed is executed after its registration date (english)
- Expected: `MATCH-DATE-001`; observed: `MATCH-DATE-001`
- Verdict: `needs_review`
  - reason: Medium: Execution date after registration date (MATCH-DATE-001)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MATCH-DATE-001` (medium, conf 0.7): Execution date after registration date — sale_deed_2009.pdf (sale_deed): execution 2009-07-01, registration 2009-06-15

### ✅ `predecessor_not_uploaded`

- Seeded error: the 1998 predecessor deed is missing from the uploads (english)
- Expected: `MH-CHAIN-001`; observed: `MH-CHAIN-001`
- Verdict: `flagged` (expected `flagged`)
  - reason: High: Ownership chain has an unevidenced step (MH-CHAIN-001)
  - reason: Ownership step 1 (Vithal More → Shantaram Pawar) is not evidenced: sale_deed_2009.pdf; mutation: ferfar_2009.pdf
- Ownership chain: 1. Vithal More → Shantaram Pawar [sale, GAP]
- Finding `MH-CHAIN-001` (high, conf 0.8): Ownership chain has an unevidenced step — Step 1: Vithal More → Shantaram Pawar (sale_deed_2009.pdf; mutation: ferfar_2009.pdf)

### ✅ `mutation_without_deed`

- Seeded error: the ferfar mutation cites a sale deed that was not uploaded (english)
- Expected: `MH-CHAIN-001`; observed: `MH-CHAIN-001`
- Verdict: `flagged` (expected `flagged`)
  - reason: High: Ownership chain has an unevidenced step (MH-CHAIN-001)
  - reason: Ownership step 2 (unknown transferor → Shantaram Pawar) is not evidenced: ferfar_2009.pdf
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. unknown → Shantaram Pawar [mutation, GAP]
- Finding `MH-CHAIN-001` (high, conf 0.8): Ownership chain has an unevidenced step — Step 2: unknown transferor → Shantaram Pawar (ferfar_2009.pdf)

### ✅ `mortgage_overlay`

- Seeded error: a mortgage deed is added to the uploads (english)
- Expected: `MH-ENC-001`; observed: `MH-ENC-001`
- Verdict: `flagged`
  - reason: High: Mortgage deed among the documents (MH-ENC-001)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MH-ENC-001` (high, conf 0.85): Mortgage deed among the documents — Mortgage deed: mortgage_deed_2019.pdf

### ✅ `will_overlay`

- Seeded error: a will is added to the uploads (english)
- Expected: `MH-SUCC-001`; observed: `MH-SUCC-001`
- Verdict: `needs_review`
  - reason: Medium: Succession document requires verification (MH-SUCC-001)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MH-SUCC-001` (medium, conf 0.8): Succession document requires verification — Succession-related documents: will_2020.pdf

### ✅ `court_overlay`

- Seeded error: a court document is added to the uploads (english)
- Expected: `MH-LIT-001`; observed: `MH-LIT-001`
- Verdict: `flagged`
  - reason: High: Court document among the documents (MH-LIT-001)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MH-LIT-001` (high, conf 0.85): Court document among the documents — Court document: court_case_2021.pdf

### ✅ `agreement_only`

- Seeded error: the only transfer document is an unregistered agreement to sale (english)
- Expected: `MH-CHAIN-002`; observed: `MH-CHAIN-002`
- Verdict: `needs_review`
  - reason: Medium: Only an agreement to sale is available (MH-CHAIN-002)
- Ownership chain: 1. Vithal More → Shantaram Pawar [agreement]
- Finding `MH-CHAIN-002` (medium, conf 0.8): Only an agreement to sale is available — Ownership chain contains only an agreement step

### ✅ `profile_identifier_mismatch`

- Seeded error: property profile says survey 999/9 (documents 221/2) (english)
- Expected: `MH-IDENT-002`; observed: `MH-IDENT-002`
- Verdict: `flagged`
  - reason: High: Profile survey number differs from documents (MH-IDENT-002)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MH-IDENT-002` (high, conf 0.85): Profile survey number differs from documents — Profile: 999/9; extracted: 221/2 in predecessor_sale_deed_1998.pdf, 221/2 in sale_deed_2009.pdf, 221/2 in ferfar_2009.pdf, 221/2 in 7_12_extract_2024.pdf, 221/2 in encumbrance_certificate_2024.pdf, 221/2 in property_card_2024.pdf

### ✅ `land_record_missing`

- Seeded error: the 7/12 extract is not uploaded (english)
- Expected: `MH-LAND-712`; observed: `MH-LAND-712`
- Verdict: `flagged`
  - reason: High: 7/12 extract not found (MH-LAND-712)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MH-LAND-712` (high, conf 0.9): 7/12 extract not found — No document classified as 7/12 among the uploads

### ✅ `hash_tampered`

- Seeded error: one document's stored hash no longer matches (metadata flip) (english)
- Expected: `MH-INTEGRITY-001`; observed: `MATCH-INTEGRITY-001`, `MH-INTEGRITY-001`
- Verdict: `flagged` (expected `flagged`)
  - reason: Critical: Hash verification failed (MATCH-INTEGRITY-001)
  - reason: Critical: Registered hash does not match the file (MH-INTEGRITY-001)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MATCH-INTEGRITY-001` (critical, conf 0.95): Hash verification failed — sale_deed_2009.pdf (sale_deed): stored hash mismatch on verification
- Finding `MH-INTEGRITY-001` (critical, conf 0.95): Registered hash does not match the file — Hash mismatch on: sale_deed_2009.pdf

### ✅ `village_mismatch`

- Seeded error: 7/12 extract is for a different village (Undri) (english)
- Expected: `MATCH-VILLAGE-001`; observed: `MATCH-VILLAGE-001`
- Verdict: `needs_review`
  - reason: Medium: Village mismatch across documents (MATCH-VILLAGE-001)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MATCH-VILLAGE-001` (medium, conf 0.7): Village mismatch across documents — Wagholi in predecessor_sale_deed_1998.pdf (sale_deed), sale_deed_2009.pdf (sale_deed), ferfar_2009.pdf (ferfar), encumbrance_certificate_2024.pdf (ec), property_card_2024.pdf (property_card); Undri in 7_12_extract_2024.pdf (7_12_extract)

### ✅ `gat_mismatch`

- Seeded error: 1998 deed prints Gat No. 512 instead of 318 (english)
- Expected: `MATCH-GAT-001`; observed: `MATCH-GAT-001`, `MH-IDENT-002`
- Verdict: `flagged`
  - reason: High: Gat Number mismatch across documents (MATCH-GAT-001)
  - reason: High: Profile gat number differs from documents (MH-IDENT-002)
- Ownership chain: 1. Dagdu Shinde → Vithal More [sale]; 2. Vithal More → Shantaram Pawar [sale]
- Finding `MATCH-GAT-001` (high, conf 0.85): Gat Number mismatch across documents — 318 in sale_deed_2009.pdf (sale_deed), 7_12_extract_2024.pdf (7_12_extract); 512 in predecessor_sale_deed_1998.pdf (sale_deed)
- Finding `MH-IDENT-002` (high, conf 0.85): Profile gat number differs from documents — Profile: 318; extracted: 512 in predecessor_sale_deed_1998.pdf

### ✅ `control_clean__mr`

- Seeded error: nothing: internally consistent control (marathi)
- Expected: — (control); observed: —
- Verdict: `verified` (expected `verified`)
  - reason: No ownership, identity, area, encumbrance or document-integrity findings were raised by the automated checks.
- Ownership chain: 1. दगडू शिंदे → विठ्ठल मोरे [sale]; 2. विठ्ठल मोरे → शंताराम पवार [sale]

### ✅ `survey_mismatch__mr`

- Seeded error: 7/12 extract prints survey number 221/3 (marathi)
- Expected: `MATCH-SURVEY-001`; observed: `MATCH-SURVEY-001`, `MH-IDENT-002`
- Verdict: `flagged`
  - reason: High: Survey Number mismatch across documents (MATCH-SURVEY-001)
  - reason: High: Profile survey number differs from documents (MH-IDENT-002)
- Ownership chain: 1. दगडू शिंदे → विठ्ठल मोरे [sale]; 2. विठ्ठल मोरे → शंताराम पवार [sale]
- Finding `MATCH-SURVEY-001` (high, conf 0.85): Survey Number mismatch across documents — 221/2 in predecessor_sale_deed_1998.pdf (sale_deed), sale_deed_2009.pdf (sale_deed), ferfar_2009.pdf (ferfar), encumbrance_certificate_2024.pdf (ec), property_card_2024.pdf (property_card); 221/3 in 7_12_extract_2024.pdf (7_12_extract)
- Finding `MH-IDENT-002` (high, conf 0.85): Profile survey number differs from documents — Profile: 221/2; extracted: 221/3 in 7_12_extract_2024.pdf

### ✅ `predecessor_not_uploaded__mr`

- Seeded error: the 1998 predecessor deed is missing from the uploads (marathi)
- Expected: `MH-CHAIN-001`; observed: `MH-CHAIN-001`
- Verdict: `flagged` (expected `flagged`)
  - reason: High: Ownership chain has an unevidenced step (MH-CHAIN-001)
  - reason: Ownership step 1 (विठ्ठल मोरे → शंताराम पवार) is not evidenced: sale_deed_2009.pdf
- Ownership chain: 1. विठ्ठल मोरे → शंताराम पवार [sale, GAP]
- Finding `MH-CHAIN-001` (high, conf 0.8): Ownership chain has an unevidenced step — Step 1: विठ्ठल मोरे → शंताराम पवार (sale_deed_2009.pdf)

## Limitations (honest list)

- The corpus is generated as digital text-layer PDFs: extraction accuracy on
  scanned/Marathi documents is measured separately by the AC-2 report. AC-3
  measures the consistency/ownership/rule/verdict logic on top of the pipeline.
- Fixture wording and the pattern pack share label conventions (documented in
  ``scripts/make_fixtures.py``); the independent AC dataset is Phase 10 work.
- The hash-tamper case flips the stored verification result at the metadata
  level (as if ``/blockchain/verify`` had reported MISMATCH); producing that state
  from a real on-chain record is Phase 5 work.
- Findings are screening indicators for a reviewer, not legal determinations
  (Conflict-Handling rule, master plan 1.4).
