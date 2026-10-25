# PropChain-AI — ten-minute demo runbook

This runbook assumes the local app is running at <http://localhost:3000> with the backend at
<http://127.0.0.1:8000>. Start it with `scripts\start-app.ps1` or the two-terminal manual path in
the README.

The demo is a **screening review**, not a legal title opinion. Say that once at the start and keep
the *not checked* list visible when discussing the verdict.

## 1. Accounts

| Role | Email | Password |
|---|---|---|
| Buyer / owner | `demo@propchainai.com` | `demo1234` |
| Reviewer | `reviewer@propchainai.com` | `review1234` |
| Admin | `admin@propchainai.com` | `admin1234` |

If these accounts do not exist, run from `backend/`:

```powershell
.venv\Scripts\python.exe scripts\seed_demo_roles.py
```

Public registration only creates buyers/owners. Reviewer and admin accounts are provisioned by the
operator script.

## 2. Owner story — verified property

1. Sign in as the buyer/owner.
2. Open **Portfolio**. The demo database has three properties:
   - *Wagholi - reviewed sample deed set* — verified and already reviewed.
   - *Wagholi - missing predecessor deed* — flagged and awaiting review.
   - *Wagholi - clean title control* — verified and awaiting review.
3. Open *Wagholi - reviewed sample deed set*.
4. Point out the screening verdict, the risk indicator, and the **Not checked** panel. The verdict is
   a screening output; unknown checks remain visible rather than being treated as passes.
5. Scroll to **Human review** and show the reviewer note, the confirmed run, and **Run history**.
6. Scroll to **Documents**. Six documents are processed and fingerprint-anchored in mock mode. Show
   `MOCK · NOT A CHAIN WRITE`, `MOCK ANCHOR`, and `VERIFIED`. Use **Verify hash** on one file.
7. Open the **Ownership** section and show the evidenced transfer chain and any gaps.

## 3. Flagged story

1. Return to **Portfolio** and open *Wagholi - missing predecessor deed*.
2. The system verdict is **Flagged**. The reasons name the unevidenced ownership step and cite the
   document.
3. Sign in as the reviewer (`reviewer@propchainai.com` / `review1234`).
4. Open **Review queue**. The default **Awaiting review** filter shows two runs.
5. Open the flagged property. Show the reviewer-only **Finding review** controls and the run decision
   panel.
6. Demonstrate a finding disposition:
   - choose **Request evidence** or **Dismiss** and show that a note is required;
   - save a note, or leave it unsaved if you do not want to mutate the demo.
7. Demonstrate the run decision:
   - **Confirm** keeps the system verdict;
   - **Override** requires a final verdict;
   - every decision requires a note.
8. Do not review a stale run: open a property with an older run and note that the API returns `409`
   instead of changing history.

The owner can see the reviewer note after a decision, but reviewer-only mutation controls are hidden
from the owner.

## 4. Admin story — rule catalogue

1. Sign in as the admin (`admin@propchainai.com` / `admin1234`).
2. Open **Rules**. The catalogue is public to read; admin mode adds editing controls.
3. Show the pack summary: 14 active rules, 12 machine-evaluable, 2 metadata-only, and the pack
   signature.
4. Expand **Show condition** on a rule to show the declarative condition.
5. Open a rule editor, make a small change, and save. The save creates a new version snapshot.
6. Open **Version history** and show that the previous version is still available for rollback.
7. If you roll back, note that it creates a new version rather than deleting the current one.
8. Mention the failure mode: if every evaluable rule is removed, analysis raises `PACK-EMPTY-001`,
   not a clean verdict.

## 5. Optional — real chain mode

For a live EVM demo, follow the README's **Blockchain anchoring** section. The short version:

```powershell
cd contracts
npm run node          # terminal 1
npm run deploy:local  # terminal 2
```

Set `BLOCKCHAIN_MOCK_MODE=false`, the deployed contract address, the chain id, and a funded Hardhat
private key in `backend\.env`, then restart the backend. Anchor and verify a document. Stop the node
or remove the key to demonstrate that the feature fails closed; it should not pretend to succeed.

Restore `BLOCKCHAIN_MOCK_MODE=true` and restart before handing the machine over.

## 6. Reset the demo

- To reset only the rule catalogue, use **Reset** in admin mode. It restores the built-in pack.
- To reset the local database, stop the backend and replace `backend\propchain.db` with a fresh
  migrated database. Do not delete a database you still need; keep a copy outside the repository.
- Re-run `scripts\seed_demo_roles.py` after recreating the database.
- Upload the six files in `docs/samples` to recreate the clean verified property.

## 7. Troubleshooting

| Symptom | Check |
|---|---|
| Frontend cannot reach API | Backend is on port 8000; `NEXT_PUBLIC_API_URL` is correct |
| Reviewer sees no queue | Runs need a completed verdict; the queue is latest-run only |
| A review returns `409` | The run is stale; reload the property and use the latest run |
| Chain status is mock | `BLOCKCHAIN_MOCK_MODE=true`; restart after changing `.env` |
| Chain status errors | Hardhat node, contract address, chain id, and funded key |
| OCR skips scans | Tesseract path and `TESSDATA_PREFIX` in `backend\.env` |
| Rule analysis fails | The active pack has no evaluable rules; restore the pack |

## 8. Demo boundaries

- The fixtures are synthetic and co-designed. They are not a measure of general legal accuracy.
- The PDF report is a screening report, not a title certificate.
- A hash anchor proves integrity, not ownership.
- The reviewer decision is a human record on top of the screening output; it does not turn the
  system into a legal authority.
