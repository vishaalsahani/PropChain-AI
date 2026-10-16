# Phase 2 — AC-2 labelled-fixture accuracy report

- Generated: 2026-10-16 21:03 UTC
- Fixtures: `C:\Users\visha\AppData\Local\Temp\propchain_fixtures` (18 documents)
- Engines: ocr=`tesseract-5.5.3`, classifier=`keyword-v1`, nlp=`patterns-v1`

## Headline

- Document classification: 18/18 (100.0%)
- AC-2 core fields (owner / survey / area / date): **54/54 (100.0%)**
- All scored fields: 136/136 (100.0%)

## By language and variant

| group | docs | classification | AC-2 core | all scored fields |
|---|---|---|---|---|
| English | 9 | 9/9 (100.0%) | 26/26 (100.0%) | 67/67 (100.0%) |
| Marathi | 9 | 9/9 (100.0%) | 28/28 (100.0%) | 69/69 (100.0%) |
| Digital (text layer) | 8 | 8/8 (100.0%) | 24/24 (100.0%) | 62/62 (100.0%) |
| Scanned (image OCR) | 10 | 10/10 (100.0%) | 30/30 (100.0%) | 74/74 (100.0%) |
| All | 18 | 18/18 (100.0%) | 54/54 (100.0%) | 136/136 (100.0%) |

## Per document

### `sale_deed_01_en_scanned.pdf`

- Expected type `sale_deed` → predicted `sale_deed` (OK); OCR language `english`, pages 2.

| field | expected | extracted | match |
|---|---|---|---|
| `seller_name` | Kavita Pawar | Kavita Pawar | ✅ |
| `buyer_name` | Dattatray Bhosale | Dattatray Bhosale | ✅ |
| `survey_number` | 33/1B | 33/1B | ✅ |
| `gat_number` | 96 | 96 | ✅ |
| `area_sqft` | 950.0 | 950 | ✅ |
| `registration_date` | 2020-09-24 | 2020-09-24 | ✅ |
| `registration_number` | MH-PUN-2020-53021 | MH-PUN-2020-53021 | ✅ |
| `consideration_amount` | 2250000.0 | 2250000 | ✅ |
| `village` | Undri | Undri | ✅ |
| `taluka` | Mulshi | Mulshi | ✅ |
| `district` | Pune | Pune | ✅ |
- Note: Deed names the parties only: seller_name/buyer_name are the parties; no owner_name label is printed.

### `sale_deed_02_mr_digital.pdf`

- Expected type `sale_deed` → predicted `sale_deed` (OK); OCR language `marathi`, pages 2.

| field | expected | extracted | match |
|---|---|---|---|
| `seller_name` | मीना कुलकर्णी | मीना कुलकर्णी | ✅ |
| `buyer_name` | दत्तात्रय भोसले | दत्तात्रय भोसले | ✅ |
| `survey_number` | 145/2A | 145/2A | ✅ |
| `gat_number` | 210/2 | 210/2 | ✅ |
| `area_sqft` | 1250.0 | 1250 | ✅ |
| `registration_date` | 2019-09-12 | 2019-09-12 | ✅ |
| `registration_number` | MH-PUN-2019-75918 | MH-PUN-2019-75918 | ✅ |
| `consideration_amount` | 1250000.0 | 1250000 | ✅ |
| `village` | वाघोली | वाघोली | ✅ |
| `taluka` | हवेली | हवेली | ✅ |
| `district` | नाशिक | नाशिक | ✅ |
- Note: Deed names the parties only: seller_name/buyer_name are the parties; no owner_name label is printed.

### `agreement_to_sale_03_en_digital.pdf`

- Expected type `agreement_to_sale` → predicted `agreement_to_sale` (OK); OCR language `english`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `seller_name` | Prakash Gaikwad | Prakash Gaikwad | ✅ |
| `buyer_name` | Rajesh Patil | Rajesh Patil | ✅ |
| `survey_number` | 267/4 | 267/4 | ✅ |
| `gat_number` | 210/2 | 210/2 | ✅ |
| `area_sqft` | 1250.0 | 1250 | ✅ |
| `consideration_amount` | 875000.0 | 875000 | ✅ |
| `village` | Wagholi | Wagholi | ✅ |
| `taluka` | Mulshi | Mulshi | ✅ |
| `district` | Nashik | Nashik | ✅ |
- Note: Agreement is unregistered: no registration number/date by design; owner_name not printed (parties only).

### `agreement_to_sale_04_mr_scanned.pdf`

- Expected type `agreement_to_sale` → predicted `agreement_to_sale` (OK); OCR language `marathi`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `seller_name` | सुनीता मोरे | सुनीता मोरे | ✅ |
| `buyer_name` | कविता पवार | कविता पवार | ✅ |
| `survey_number` | 124/A | 124/A | ✅ |
| `gat_number` | 456 | 456 | ✅ |
| `area_sqft` | 1250.0 | 1250 | ✅ |
| `consideration_amount` | 875000.0 | 875000 | ✅ |
| `village` | तळेगाव | तळेगाव | ✅ |
| `taluka` | खेड | खेड | ✅ |
| `district` | पुणे | पुणे | ✅ |
- Note: Agreement is unregistered: no registration number/date by design; owner_name not printed (parties only).

### `gift_deed_05_en_scanned.pdf`

- Expected type `gift_deed` → predicted `gift_deed` (OK); OCR language `english`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `seller_name` | Kavita Pawar | Kavita Pawar | ✅ |
| `buyer_name` | Meena Kulkarni | Meena Kulkarni | ✅ |
| `survey_number` | 92 | 92 | ✅ |
| `area_sqft` | 9900.0 | 9900 | ✅ |
| `registration_date` | 2020-11-06 | 2020-11-06 | ✅ |
| `registration_number` | MH-PUN-2020-27948 | MH-PUN-2020-27948 | ✅ |
| `consideration_amount` | 51000.0 | 51000 | ✅ |
| `village` | Wagholi | Wagholi | ✅ |
| `taluka` | Khed | Khed | ✅ |
| `district` | Pune | Pune | ✅ |
- Note: No donor/donee fields in the canonical vocabulary: seller_name = donor, buyer_name = donee. Area printed in sq.yd (converted to sq.ft).

### `gift_deed_06_mr_digital.pdf`

- Expected type `gift_deed` → predicted `gift_deed` (OK); OCR language `marathi`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `seller_name` | राजेश पाटील | राजेश पाटील | ✅ |
| `buyer_name` | अनिल जाधव | अनिल जाधव | ✅ |
| `survey_number` | 92 | 92 | ✅ |
| `area_sqft` | 8550.0 | 8550 | ✅ |
| `registration_date` | 2023-12-19 | 2023-12-19 | ✅ |
| `registration_number` | MH-PUN-2023-52645 | MH-PUN-2023-52645 | ✅ |
| `consideration_amount` | 51000.0 | 51000 | ✅ |
| `village` | वाकड | वाकड | ✅ |
| `taluka` | हवेली | हवेली | ✅ |
| `district` | पुणे | पुणे | ✅ |
- Note: No donor/donee fields in the canonical vocabulary: seller_name = donor, buyer_name = donee. Area printed in sq.yd (converted to sq.ft).

### `7_12_extract_07_en_digital.pdf`

- Expected type `7_12_extract` → predicted `7_12_extract` (OK); OCR language `english`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | Sunita More | Sunita More | ✅ |
| `survey_number` | 267/4 | 267/4 | ✅ |
| `gat_number` | 78 | 78 | ✅ |
| `area_sqft` | 26898.3 | 26898.3 | ✅ |
| `village` | Baner | Baner | ✅ |
| `taluka` | Shirur | Shirur | ✅ |
| `district` | Nashik | Nashik | ✅ |
- Note: 7/12 extract: the printed 'Extract Date' is an issue date, deliberately not ground truth; there is no registration date on this document.

### `7_12_extract_08_mr_scanned.pdf`

- Expected type `7_12_extract` → predicted `7_12_extract` (OK); OCR language `marathi`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | राजेश पाटील | राजेश पाटील | ✅ |
| `survey_number` | 56/2 | 56/2 | ✅ |
| `gat_number` | 512 | 512 | ✅ |
| `area_sqft` | 43593.8 | 43593.795000000006 | ✅ |
| `village` | खराडी | खराडी | ✅ |
| `taluka` | मुळशी | मुळशी | ✅ |
| `district` | सातारा | सातारा | ✅ |
- Note: 7/12 extract: the printed 'Extract Date' is an issue date, deliberately not ground truth; there is no registration date on this document.

### `8a_record_09_en_scanned.pdf`

- Expected type `8a_record` → predicted `8a_record` (OK); OCR language `english`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | Anil Jadhav | Anil Jadhav | ✅ |
| `survey_number` | 56/2 | 56/2 | ✅ |
| `area_sqft` | 65336.87 | 65336.873 | ✅ |
| `village` | Wakad | Wakad | ✅ |
| `taluka` | Shirur | Shirur | ✅ |
| `district` | Satara | Satara | ✅ |
- Note: 8A record: holder only; no Gat number, no registration date printed.

### `8a_record_10_mr_digital.pdf`

- Expected type `8a_record` → predicted `8a_record` (OK); OCR language `marathi`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | अश्विनी जगताप | अश्विनी जगताप | ✅ |
| `survey_number` | 33/1B | 33/1B | ✅ |
| `area_sqft` | 65336.87 | 65336.873 | ✅ |
| `village` | खराडी | खराडी | ✅ |
| `taluka` | खेड | खेड | ✅ |
| `district` | सातारा | सातारा | ✅ |
- Note: 8A record: holder only; no Gat number, no registration date printed.

### `ferfar_11_en_digital.pdf`

- Expected type `ferfar` → predicted `ferfar` (OK); OCR language `english`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | Dattatray Bhosale | Dattatray Bhosale | ✅ |
| `survey_number` | 56/2 | 56/2 | ✅ |
| `area_sqft` | 32670.0 | 32670 | ✅ |
| `registration_date` | 2022-01-19 | 2022-01-19 | ✅ |
| `registration_number` | MH-PUN-2022-26478 | MH-PUN-2022-26478 | ✅ |
| `village` | Wagholi | Wagholi | ✅ |
| `district` | Pune | Pune | ✅ |
- Note: ferfar: registration_date is the mutation (ferfar) entry date; the registration number is the referenced sale deed.

### `ferfar_12_mr_scanned.pdf`

- Expected type `ferfar` → predicted `ferfar` (OK); OCR language `marathi`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | प्रकाश गायकवाड | प्रकाश गायकवाड | ✅ |
| `survey_number` | 124/A | 124/A | ✅ |
| `area_sqft` | 26898.3 | 26898.3 | ✅ |
| `registration_date` | 2022-02-13 | 2022-02-13 | ✅ |
| `registration_number` | MH-PUN-2022-58347 | MH-PUN-2022-58347 | ✅ |
| `village` | वाकड | वाकड | ✅ |
| `district` | पुणे | पुणे | ✅ |
- Note: ferfar: registration_date is the mutation (ferfar) entry date; the registration number is the referenced sale deed.

### `property_card_13_en_scanned.pdf`

- Expected type `property_card` → predicted `property_card` (OK); OCR language `english`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | Rajesh Patil | Rajesh Patil | ✅ |
| `cts_number` | 567 | 567 | ✅ |
| `area_sqft` | 484.38 | 484.3755 | ✅ |
| `village` | Talegaon | Talegaon | ✅ |
| `district` | Satara | Satara | ✅ |
- Note: Property card: city-survey record; CTS number instead of survey number, no registration date.

### `property_card_14_mr_digital.pdf`

- Expected type `property_card` → predicted `property_card` (OK); OCR language `marathi`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | कविता पवार | कविता पवार | ✅ |
| `cts_number` | 567 | 567 | ✅ |
| `area_sqft` | 484.38 | 484.3755 | ✅ |
| `village` | उंड्री | उंड्री | ✅ |
| `district` | पुणे | पुणे | ✅ |
- Note: Property card: city-survey record; CTS number instead of survey number, no registration date.

### `ec_15_en_digital.pdf`

- Expected type `ec` → predicted `ec` (OK); OCR language `english`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | Dattatray Bhosale | Dattatray Bhosale | ✅ |
| `survey_number` | 78/3 | 78/3 | ✅ |
| `area_sqft` | 10890.0 | 10890 | ✅ |
| `registration_date` | 2023-10-18 | 2023-10-18 | ✅ |
| `registration_number` | MH-PUN-2023-85520 | MH-PUN-2023-85520 | ✅ |
| `village` | Undri | Undri | ✅ |
| `district` | Pune | Pune | ✅ |
- Note: EC: registration number/date belong to the encumbrance (mortgage) entry.

### `ec_16_mr_scanned.pdf`

- Expected type `ec` → predicted `ec` (OK); OCR language `marathi`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | सुरेश देशमुख | सुरेश देशमुख | ✅ |
| `survey_number` | 92 | 92 | ✅ |
| `area_sqft` | 26586.83 | 26586.833 | ✅ |
| `registration_date` | 2015-08-07 | 2015-08-07 | ✅ |
| `registration_number` | MH-PUN-2015-87773 | MH-PUN-2015-87773 | ✅ |
| `village` | खराडी | खराडी | ✅ |
| `district` | नाशिक | नाशिक | ✅ |
- Note: EC: registration number/date belong to the encumbrance (mortgage) entry.

### `ferfar_17_mr_scanned.jpg`

- Expected type `ferfar` → predicted `ferfar` (OK); OCR language `marathi`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | अश्विनी जगताप | अश्विनी जगताप | ✅ |
| `survey_number` | 33/1B | 33/1B | ✅ |
| `area_sqft` | 13612.5 | 13612.5 | ✅ |
| `registration_date` | 2022-12-02 | 2022-12-02 | ✅ |
| `registration_number` | MH-PUN-2022-38888 | MH-PUN-2022-38888 | ✅ |
| `village` | उंड्री | उंड्री | ✅ |
| `district` | सातारा | सातारा | ✅ |
- Note: ferfar: registration_date is the mutation (ferfar) entry date; the registration number is the referenced sale deed.

### `property_card_18_en_scanned.png`

- Expected type `property_card` → predicted `property_card` (OK); OCR language `english`, pages 1.

| field | expected | extracted | match |
|---|---|---|---|
| `owner_name` | Nilesh Chavan | Nilesh Chavan | ✅ |
| `cts_number` | 1234 | 1234 | ✅ |
| `area_sqft` | 672.74 | 672.74375 | ✅ |
| `village` | Wakad | Wakad | ✅ |
| `district` | Pune | Pune | ✅ |
- Note: Property card: city-survey record; CTS number instead of survey number, no registration date.

## Limitations (honest list)

- The fixture wording shares label conventions with the pattern packs, so this
  corpus measures the end-to-end pipeline (render/scan → OCR → classify →
  extract → normalize), not generalisation to unseen wording. The full AC
  dataset with independent ground truth is Phase 10 work.
- Names are compared fuzzily (≥85) because OCR of Devanagari names can differ
  in one conjunct; identifiers and dates are compared exactly.
- `area_sqft` tolerance is 5% to absorb digit-script rounding; the fixture
  generator prints areas the normalizer can parse exactly.
