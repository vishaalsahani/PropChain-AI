# PropChain-AI — Miniature Web App

Blockchain-based AI system for property document analysis (academic prototype).

## Project Structure

```
PropChain/
├── backend/          # FastAPI REST API
├── frontend/         # Next.js + TypeScript + Tailwind
├── contracts/        # Solidity document registry
├── docker-compose.yml
└── .env.example
```

## Components Included

| Component | Status | Description |
|-----------|--------|-------------|
| Auth (JWT) | Working | Register, login, protected routes |
| Property Management | Working | Create/list/view properties |
| Document Upload | Working | PDF/JPG/PNG upload + SHA-256 hash |
| OCR/NLP Pipeline | Working | Real engines (Phase 2): Tesseract OCR + PDF text layer, keyword doc classifier (15 types, EN/MR), pattern-based field extraction |
| Analysis Engine | Partial | Consistency checks run on extracted values; the ownership-chain builder is still the Phase-1 demo chain (real builder: Phase 3) |
| Rule Engine | Stub | Maharashtra demo rules (DB-backed rule packs: Phase 4) |
| Blockchain Module | Stub/Mock | Hash register + verify (mock mode default) |
| Report Generator | Working | PDF due-diligence report download |
| Frontend Dashboard | Working | Full UI for all flows |

## Quick Start (Local)

### 1. Backend

Requires Python 3.12 (3.13+ untested).

```powershell
cd backend
uv venv --python 3.12 .venv                                  # or: python -m venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### 2. Frontend

Requires Node 20+ (project runs Next 16 + React 19).

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

### 3. Environment

Copy `.env.example` to `.env` in project root and adjust if needed.

Optional system tool: **Tesseract OCR** — required for scanned-document OCR (digital PDFs use
their text layer). If the binary is not on `PATH`, point `TESSERACT_CMD` at it in `.env`.

### Engine selection (Phases 2–3)

Document intelligence sits behind frozen interfaces (`backend/app/services/interfaces.py`) and is
selected per machine in `backend/.env` (read when the server runs from `backend/`):

| Setting | Values | Code default | Effect |
|---|---|---|---|
| `OCR_ENGINE` | `fake`, `tesseract` | `fake` | Tesseract OCR for scans; digital PDFs use their embedded text layer |
| `DOC_CLASSIFIER_ENGINE` | `fake`, `keyword` | `fake` | Keyword/label fingerprinting → one of the 15 doc types |
| `NLP_EXTRACTOR_ENGINE` | `fake`, `patterns` | `fake` | Label/regex pattern pack, EN + Marathi (Devanagari numerals, `MH-XXX-YYYY-NNNNN`, survey/Gat/CTS, area units → sqft, consideration) |
| `CROSS_VALIDATOR_ENGINE` | `fake`, `matrix` | `fake` | Cross-document consistency matrix (`matrix-v1`): identifiers, names, places, area (±5%), boundaries, registration numbers, date order, hash verification — every finding cites both documents |
| `OWNERSHIP_BUILDER_ENGINE` | `fake`, `evidence` | `fake` | Evidence-based ownership chain (`evidence-v1`): transfer events from deeds, ferfar mutations corroborate their deed, land records fall back to a current-holder node, unevidenced links get `gap_flag` |
| `RULE_ENGINE` | `fake`, `mh_pack` | `fake` | Maharashtra rule pack (`mh-v1`): 12 screening rules (missing 7/12, identifier clash, chain gaps, mortgage, succession, litigation, area, hash mismatch) |

The active selection is visible in `GET /health`. The default is `fake` so a fresh checkout boots
without Tesseract/OpenCV; a real-engine dev machine sets `tesseract` / `keyword` / `patterns` /
`matrix` / `evidence` / `mh_pack`. An unknown engine name logs a warning and falls back to fake; a
known name whose module cannot be imported raises at first use (loud failure, never a silent mock).

Each analysis run records its verdict (**Verified / Needs Review / Flagged**, `GET /analysis/{id}/verdict`)
together with machine-readable reasons, including an explicit *not checked* list (RERA, litigation
history, …) so unknowns are stated instead of guessed — see `backend/app/services/verdict.py` for the
documented mapping from findings to verdict.

### Labelled fixtures + AC-2 accuracy harness

`backend/scripts/make_fixtures.py` deterministically generates an 18-document English/Marathi corpus
(digital PDFs with a text layer plus scanned PDF/JPEG/PNG variants with rotation, noise and JPEG
artifacts) across 6 document types, with ground-truth JSON and a `_manifest.json`:

```powershell
cd backend
.venv\Scripts\python.exe scripts\make_fixtures.py --verify    # writes %TEMP%\propchain_fixtures
.venv\Scripts\python.exe scripts\accuracy_report.py           # score the real engines from .env
.venv\Scripts\python.exe scripts\accuracy_report.py --fake    # smoke-run the harness itself
```

The harness drives the real pipeline (OCR → classify → extract) and scores it against the ground
truth, writing `backend/artifacts/phase2_accuracy.md` (+ `.json`). Measured on this machine
(Tesseract 5.5.3 + `keyword-v1` + `patterns-v1`, 2026-10-17): **classification 18/18 · AC-2 core
fields (owner / survey / area / date) 54/54 · all scored fields 136/136**, for English and Marathi,
digital and scanned.

> Honesty note: the fixture wording and the pattern pack were co-designed (see the `make_fixtures.py`
> docstring), so this measures the end-to-end pipeline, not generalisation to unseen wording. The
> independent acceptance dataset is Phase 10 work.

### Seeded-error corpus + AC-3 detection harness

`backend/scripts/make_error_set.py` generates 21 coherent per-property document sets (6 base
documents each: two chained sale deeds, ferfar, 7/12 extract, NIL encumbrance certificate, property
card). Every error case differs from the clean control by exactly one seeded inconsistency — survey
mismatch, owner mismatch, area drift, boundary change, reused registration number, execution after
registration, missing predecessor deed, mutation without its deed, mortgage/will/court overlays,
agreement-only chain, profile-vs-document identifier clash, missing 7/12, hash mismatch, village/Gat
mismatch — with the control and two error cases also generated in Marathi:

```powershell
cd backend
.venv\Scripts\python.exe scripts\make_error_set.py      # writes %TEMP%\propchain_errorset
.venv\Scripts\python.exe scripts\ac3_report.py          # score the real pipeline (needs Tesseract)
```

The harness runs the real chain (OCR → classify → extract → `matrix-v1` → `evidence-v1` → `mh-v1` →
verdict) over each case and writes `backend/artifacts/phase3_ac3.md` (+ `.json`). Measured on this
machine (2026-10-17): **AC-3 seeded-error detection 19/19 (100%, target ≥90%) · both controls clean
(no false positives) · pinned verdicts 6/6**. Limitations (digital corpus, co-designed wording,
metadata-level hash flip) are listed in the report itself.

### 4. Contracts (optional local EVM)

```powershell
cd contracts
npm install
npm run compile        # compile DocumentRegistry.sol (solc 0.8.20)
npm run test           # hardhat contract tests
npm run node           # terminal 1: local chain on http://127.0.0.1:8545
npm run deploy:local   # terminal 2: deploy; writes deployments/localhost.json
```

## Docker (Full Stack)

```powershell
docker compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- PostgreSQL: localhost:5432
- Ganache: localhost:8545

> Docker is optional — the project runs fully with the local Python/Node setup above.
> The `ganache` service is a legacy image (Truffle Suite was sunset in 2023); for local
> chain development prefer `npm run node` inside `contracts/` (Hardhat).

## Demo Workflow

1. Register a new account at `/register`
2. Create a property profile
3. Upload 1–2 property documents (any PDF/image)
4. Click **Run Analysis** to generate findings, an ownership chain and a due-diligence verdict
   (Verified / Needs Review / Flagged, with reasons and a "not checked" list)
5. Click **Register Hash** / **Verify** on a document for blockchain demo
6. Download the PDF due-diligence report

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT token |
| POST | `/properties` | Create property |
| GET | `/properties` | List properties |
| POST | `/documents/upload/{id}` | Upload document |
| POST | `/analysis/run/{id}` | Run analysis (findings, ownership chain, verdict) |
| GET | `/analysis/{id}/verdict` | Latest verdict + reasons + not-checked list |
| POST | `/blockchain/register/{id}` | Register document hash |
| POST | `/blockchain/verify/{id}` | Verify document integrity |
| GET | `/reports/{id}/pdf` | Download report |

## Team

 Vishal Sahani

## Disclaimer

This system provides AI-assisted documentary analysis only. It does not establish legal title or replace professional legal advice.

## Setup on a new machine

Target platform: Windows + PowerShell. (The local Python/Node path below is the supported one;
the `docker-compose.yml` route is **unsupported until Phase 5** — see the Docker note at the end of
this section.)

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.12 (3.13+ untested) | used via the project virtualenv |
| [uv](https://docs.astral.sh/uv/) | any recent | creates the venv and installs backend deps |
| Node.js + npm | Node 20+ | Next 16 + React 19, Hardhat |

Optional: [micromamba](https://mamba.readthedocs.io/) for the Tesseract OCR binary (scanned
documents only).

### 1. Bootstrap (idempotent)

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

`scripts\setup.ps1` checks that `uv`/`node`/`npm` exist, creates `backend\.venv` with
`uv venv --python 3.12` when it is missing, installs `backend\requirements.txt`, then runs
`npm ci` in `frontend\` and `contracts\`. It is safe to re-run and never starts a server.
Skip parts with `-SkipBackend`, `-SkipFrontend` or `-SkipContracts`.

### 2. Environment file

```powershell
Copy-Item .env.example .env
```

`.env` lives in the project root and is read by the backend (`pydantic-settings`) and the
frontend (`NEXT_PUBLIC_API_URL`). At minimum change `SECRET_KEY`; real environment variables
always win over the `.env` file. (`.env` is resolved relative to the working directory, so a
backend shell started in `backend\` reads `backend\.env` — that is where the Phase-2 engine
selection below is kept on the demo machine. Both locations are gitignored.)

### 3. Tesseract OCR (optional)

Only needed for scanned documents — digital PDFs use their own text layer. The binary is a system
package, not a pip package:

```powershell
micromamba create -y -p C:\Users\visha\tools\tessenv -c conda-forge tesseract
```

Then point `.env` at it (already the default in `.env.example`):

```ini
TESSERACT_CMD=C:\Users\visha\tools\tessenv\Library\bin\tesseract.exe
TESSDATA_PREFIX=C:\Users\visha\tools\tessenv\share\tessdata
```

If Tesseract is missing entirely the app still runs; image-only documents simply are not OCR'd.

### 4. Run the app

```powershell
# terminal 1 — backend
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# terminal 2 — frontend
cd frontend
npm run dev
```

API docs: http://localhost:8000/docs · UI: http://localhost:3000

### 5. Tests

```powershell
cd backend
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m pytest tests\test_ocr_engine.py -v      # OCR engine (needs Tesseract)
```

The suite is self-contained: every test module boots the app against its own temp SQLite database
(migrated with `alembic upgrade head`) and temp storage directory, and no live server is required.
It pins the fake engines via environment variables, so the real engines never run inside `pytest`;
the real pipeline is measured by `scripts/accuracy_report.py` (see *Engine selection* above).
Current status: **142 tests, 0 failures** (Phase 2). Contract tests: `npm run test` in `contracts\`.

> **Docker is not supported yet.** `docker-compose.yml` is a Phase 5 deliverable; until then use the
> local setup above (there is no supported container workflow, and the compose file's images/ports
> are not maintained).
