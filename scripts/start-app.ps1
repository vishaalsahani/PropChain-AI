#Requires -Version 5.1
<#
.SYNOPSIS
    Starts the PropChain-AI development environment and opens it in the browser.

.DESCRIPTION
    One-click launcher for Windows. It is idempotent: anything already
    listening is reused, so clicking the desktop shortcut again simply opens
    the app.

      1. starts the FastAPI backend on 127.0.0.1:8000 (backend/.venv),
      2. starts the Next.js dev server on 127.0.0.1:3000 (`npm run dev`, so the
         browser always shows the current sources),
      3. waits until both answer, then opens the default browser,
      4. on failure shows a message box pointing at the log files.

    Server output is written to %TEMP%\propchain-logs\.

.PARAMETER BackendPort
    Backend port (default 8000).

.PARAMETER FrontendPort
    Frontend port (default 3000).

.PARAMETER Console
    Keep a console window with progress output (useful for troubleshooting).

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-app.ps1
#>
[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [switch]$Console
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$logDir = Join-Path $env:TEMP "propchain-logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Step([string]$Message) {
    if ($Console) { Write-Host "[propchain] $Message" }
}

function Test-Url([string]$Url, [int]$TimeoutSec = 3) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Wait-Url([string]$Url, [int]$Seconds, [string]$Name) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Url $Url) { return $true }
        Start-Sleep -Milliseconds 750
    }
    Write-Step "timed out waiting for $Name ($Url)"
    return $false
}

function Show-Failure([string]$Message) {
    try {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show(
            $Message,
            "PropChain-AI",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Warning
        ) | Out-Null
    } catch {
        Write-Host $Message
    }
}

try {
    $backendUrl = "http://127.0.0.1:$BackendPort"
    $frontendUrl = "http://localhost:$FrontendPort"

    # ---------------------------------------------------------------- backend
    if (-not (Test-Url "$backendUrl/health")) {
        Write-Step "starting the backend on $backendUrl"
        $python = Join-Path $backendDir ".venv\Scripts\python.exe"
        if (-not (Test-Path $python)) { $python = "python" }
        if (-not (Test-Path (Join-Path $backendDir "propchain.db"))) {
            Write-Step "running database migrations"
            Push-Location $backendDir
            try {
                & $python -m alembic upgrade head *>> (Join-Path $logDir "migrate.log")
            } finally {
                Pop-Location
            }
        }
        Start-Process -FilePath $python `
            -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$BackendPort", "--reload") `
            -WorkingDirectory $backendDir `
            -WindowStyle Hidden `
            -RedirectStandardOutput (Join-Path $logDir "backend.out.log") `
            -RedirectStandardError (Join-Path $logDir "backend.err.log")
    } else {
        Write-Step "backend already running"
    }

    # --------------------------------------------------------------- frontend
    if (-not (Test-Url $frontendUrl)) {
        Write-Step "starting the frontend dev server on $frontendUrl"
        Start-Process -FilePath "cmd.exe" `
            -ArgumentList @("/c", "npm run dev -- --port $FrontendPort") `
            -WorkingDirectory $frontendDir `
            -WindowStyle Hidden `
            -RedirectStandardOutput (Join-Path $logDir "frontend.out.log") `
            -RedirectStandardError (Join-Path $logDir "frontend.err.log")
    } else {
        Write-Step "frontend already running"
    }

    # ------------------------------------------------------------------ ready
    $backendOk = Wait-Url "$backendUrl/health" 90 "the backend"
    $frontendOk = Wait-Url "$frontendUrl/login" 180 "the frontend"

    if ($backendOk -and $frontendOk) {
        Write-Step "opening $frontendUrl"
        Start-Process $frontendUrl
        exit 0
    }

    $problem = @()
    if (-not $backendOk) { $problem += "backend ($backendUrl/health)" }
    if (-not $frontendOk) { $problem += "frontend ($frontendUrl)" }
    Show-Failure("PropChain-AI could not start: " + ($problem -join " and ") +
        ".`n`nLogs: $logDir`n`nRun scripts\start-app.ps1 -Console for details.")
    exit 1
} catch {
    Show-Failure("PropChain-AI launcher failed: $($_.Exception.Message)`n`nLogs: $logDir")
    exit 1
}
