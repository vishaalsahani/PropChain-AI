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
