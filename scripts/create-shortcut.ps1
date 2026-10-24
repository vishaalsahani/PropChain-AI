#Requires -Version 5.1
<#
.SYNOPSIS
    Creates (or refreshes) the PropChain-AI desktop shortcut.

.DESCRIPTION
    The shortcut points at scripts\start-app.ps1 using the bundled icon in
    docs\assets\propchain.ico. It is safe to run again; the existing shortcut is
    replaced.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\create-shortcut.ps1
#>
[CmdletBinding()]
param(
    [string]$Name = 'PropChain-AI'
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $PSScriptRoot 'start-app.ps1'
$icon = Join-Path $root 'docs\assets\propchain.ico'

if (-not (Test-Path $launcher)) {
    throw "Launcher not found: $launcher"
}
if (-not (Test-Path $icon)) {
    throw "Shortcut icon not found: $icon"
}

$desktop = [Environment]::GetFolderPath('Desktop')
if (-not (Test-Path $desktop)) {
    throw "Desktop folder not found: $desktop"
}

$shortcutPath = Join-Path $desktop "$Name.lnk"
$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $powershell
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcher`""
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = "$icon,0"
$shortcut.Description = 'PropChain-AI - start the development environment'
$shortcut.WindowStyle = 7
$shortcut.Save()

# Ask Explorer to pick up the new icon immediately.
try {
    Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\ie4uinit.exe') `
        -ArgumentList '-show' -WindowStyle Hidden
} catch {
    # Cosmetic only; the shortcut itself is already saved.
}

Write-Host ''
Write-Host "Created shortcut: $shortcutPath" -ForegroundColor Green
Write-Host "Icon:             $icon"
Write-Host "Target:           $launcher"
Write-Host ''
Write-Host 'Double-click the shortcut to start the backend and frontend.' -ForegroundColor White
