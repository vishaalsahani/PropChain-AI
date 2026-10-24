# Sample property documents (synthetic)

These six PDFs are **synthetic, fictional documents** created for testing PropChain-AI.
No real person, property, or government record is represented.

They form one internally consistent Maharashtra property set:

| File | Role |
|---|---|
| `predecessor_sale_deed_1998.pdf` | Root transfer: Dagdu Shinde → Vithal More |
| `sale_deed_2009.pdf` | Main transfer: Vithal More → Shantaram Pawar |
| `ferfar_2009.pdf` | Mutation entry for the 2009 sale |
| `7_12_extract_2024.pdf` | Record of rights for the current holder |
| `encumbrance_certificate_2024.pdf` | NIL encumbrance certificate |
| `property_card_2024.pdf` | City-survey property card |
| `sale-deed-preview.png` | Quick visual preview of the 2009 sale deed |

## Test the clean “Verified” case

1. Start the app and sign in (register a new account, or use the demo account if this
   machine already has the demo database: `demo@propchainai.com` / `demo1234`).
2. Choose **New property** and enter:

   | Field | Value |
   |---|---|
   | Title | Sample - Wagholi Gat 318 |
   | State | Maharashtra |
   | District | Pune |
   | Taluka | Haveli |
   | Village | Wagholi |
   | Survey No. | 221/2 |
   | Gat No. | 318 |
   | Area | 2000 sq ft |

3. Open the property and upload **all six PDFs**.
4. Click **Run analysis**.

Expected result: the ownership chain reads
`Dagdu Shinde → Vithal More → Shantaram Pawar`, the documents agree on
survey/gat/area, and the screening verdict is **Verified** with a *not checked*
list (for this set: RERA registration and court/litigation history).

Uploading only one document is a valid test too: the analysis will report the
missing land-record or chain evidence instead of returning a clean result.

## Notes

- Documents stay off-chain; only their SHA-256 hashes are registered.
- Findings are **screening indicators for a reviewer**, not legal determinations.
- The generated PDFs have a digital text layer, so they work without Tesseract.
  Scanned documents need Tesseract for OCR.
