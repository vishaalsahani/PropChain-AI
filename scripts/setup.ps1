<#
.SYNOPSIS
    Idempotent new-machine setup for PropChain-AI (Windows / PowerShell).

.DESCRIPTION
    Checks prerequisites, creates the backend virtualenv with uv when missing,
    installs backend/requirements.txt, then runs `npm ci` in frontend/ and
    contracts/. It never starts any server — run the follow-up commands printed
    at the end (or see README.md -> "Setup on a new machine") when you want to.

    Safe to re-run: existing venv/node_modules are reused, every step is skipped
    when it is already done.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

.EXAMPLE
    # backend only (skip both npm installs)
    powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -SkipFrontend -SkipContracts
#>
[CmdletBinding()]
param(
    [switch]$SkipFrontend,
    [switch]$SkipContracts,
    [switch]$SkipBackend
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot 'backend'
$FrontendDir = Join-Path $RepoRoot 'frontend'
$ContractsDir = Join-Path $RepoRoot 'contracts'
$VenvDir = Join-Path $BackendDir '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
$Requirements = Join-Path $BackendDir 'requirements.txt'

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok([string]$Message) {
    Write-Host "    $Message" -ForegroundColor Green
}

function Assert-Command([string]$Name, [string]$Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found on PATH. $Hint"
    }
}

function Assert-LastExitCode([string]$What) {
    if ($LASTEXITCODE -ne 0) {
        throw "$What failed (exit code $LASTEXITCODE)."
    }
}

Write-Host ''
Write-Host 'PropChain-AI setup' -ForegroundColor White
Write-Host "Repository: $RepoRoot"
Write-Host ''

# --- 1. prerequisites -------------------------------------------------------
Write-Step 'Checking prerequisites (uv, node, npm)'
Assert-Command 'uv' 'Install it from https://docs.astral.sh/uv/ (or: winget install astral-sh.uv).'
Assert-Command 'node' 'Install Node.js 20+ from https://nodejs.org/ (or: winget install OpenJS.NodeJS.LTS).'
Assert-Command 'npm' 'npm ships with Node.js - reinstall Node.js LTS.'
$nodeVersion = (& node --version).Trim()
Write-Ok "uv $((& uv --version).Trim().Split(' ')[1])  |  node $nodeVersion"

if (-not (Test-Path (Join-Path $RepoRoot '.env.example'))) {
    Write-Warning '.env.example is missing - the repository may be incomplete.'
}

# --- 2. backend venv + dependencies ----------------------------------------
if ($SkipBackend) {
    Write-Step 'Skipping backend (--SkipBackend)'
}
else {
    if (Test-Path $VenvPython) {
        Write-Step 'Backend virtualenv already exists - reusing backend\.venv'
    }
    else {
        Write-Step 'Creating backend virtualenv with uv (Python 3.12)'
        & uv venv --python 3.12 $VenvDir
        Assert-LastExitCode 'uv venv'
    }

    Write-Step 'Installing backend/requirements.txt into backend\.venv'
    if (-not (Test-Path $Requirements)) {
        throw "Missing $Requirements."
    }
    & uv pip install --python $VenvPython -r $Requirements
    Assert-LastExitCode 'uv pip install'
    Write-Ok "Interpreter: $VenvPython"
}

# --- 3. npm dependencies ----------------------------------------------------
if ($SkipFrontend) {
    Write-Step 'Skipping frontend (--SkipFrontend)'
}
else {
    Write-Step 'Installing frontend dependencies (npm ci)'
    Push-Location $FrontendDir
    try {
        if (-not (Test-Path (Join-Path $FrontendDir 'package-lock.json'))) {
            Write-Warning 'frontend\package-lock.json is missing - falling back to npm install.'
            & npm install
            Assert-LastExitCode 'npm install (frontend)'
        }
        else {
            & npm ci
            Assert-LastExitCode 'npm ci (frontend)'
        }
    }
    finally {
        Pop-Location
    }
}

if ($SkipContracts) {
    Write-Step 'Skipping contracts (--SkipContracts)'
}
else {
    Write-Step 'Installing contracts dependencies (npm ci)'
    Push-Location $ContractsDir
    try {
        if (-not (Test-Path (Join-Path $ContractsDir 'package-lock.json'))) {
            Write-Warning 'contracts\package-lock.json is missing - falling back to npm install.'
            & npm install
            Assert-LastExitCode 'npm install (contracts)'
        }
        else {
            & npm ci
            Assert-LastExitCode 'npm ci (contracts)'
        }
    }
    finally {
        Pop-Location
    }
}

# --- 4. next steps ----------------------------------------------------------
Write-Host ''
Write-Host 'Setup finished. Next steps (nothing was started for you):' -ForegroundColor White
Write-Host @"

  1. Environment file (project root):
       Copy-Item .env.example .env
     Adjust SECRET_KEY (any long random string is fine locally) and the OCR paths if needed.

  2. Tesseract OCR (optional; needed only for scanned/complex documents).
     Get micromamba from https://mamba.readthedocs.io/ if you do not have it yet, then:
       micromamba create -y -p C:\Users\visha\tools\tessenv -c conda-forge tesseract
     Point .env at the created env (already the default in .env.example):
       TESSERACT_CMD=C:\Users\visha\tools\tessenv\Library\bin\tesseract.exe
       TESSDATA_PREFIX=C:\Users\visha\tools\tessenv\share\tessdata

  3. Run the backend (terminal 1):
       cd backend
       .venv\Scripts\python.exe -m uvicorn app.main:app --reload
     API docs: http://localhost:8000/docs

  4. Run the frontend (terminal 2):
       cd frontend
       npm run dev
     App: http://localhost:3000

  5. Run the backend test suite (uses temp SQLite DBs, no server needed):
       cd backend
       .venv\Scripts\python.exe -m pytest

  6. Optional local EVM chain for the contracts module (two terminals):
       cd contracts
       npm run node           # terminal A
       npm run deploy:local   # terminal B

  Note: the docker-compose path is not supported until Phase 5 (see README.md).
"@
