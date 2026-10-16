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
| OCR/NLP Pipeline | Stub | Mock entity extraction for demo |
| Analysis Engine | Stub | Cross-doc compare + ownership chain |
| Rule Engine | Stub | Maharashtra demo rules |
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
4. Click **Run Analysis** to generate findings and ownership chain
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
| POST | `/analysis/run/{id}` | Run analysis |
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
always win over the `.env` file.

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
```

The suite is self-contained: every test module boots the app against its own temp SQLite database
(migrated with `alembic upgrade head`) and temp storage directory, and no live server is required.

> **Docker is not supported yet.** `docker-compose.yml` is a Phase 5 deliverable; until then use the
> local setup above (there is no supported container workflow, and the compose file's images/ports
> are not maintained).
