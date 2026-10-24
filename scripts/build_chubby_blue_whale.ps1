# build_selfuse.ps1 - One-click build: uv sync -> PyInstaller -> Inno Setup
# Usage: powershell -ExecutionPolicy Bypass -File scripts\build_selfuse.ps1
#
# Prerequisites:
#   - uv installed (https://docs.astral.sh/uv/)
#   - Inno Setup 7 at D:\Tool\Inno Setup 7

$ErrorActionPreference = "Stop"
$ISCC = "D:\Tool\Inno Setup 7\ISCC.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  dsh-pet-chubby_blue_whale build (v4.4.0)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# --- Step 1: Install dependencies ---
Write-Host "`n[1/4] uv sync + pyinstaller" -ForegroundColor Yellow
uv sync
if ($LASTEXITCODE -ne 0) { Write-Error "uv sync failed"; exit 1 }
uv pip install pyinstaller packaging
if ($LASTEXITCODE -ne 0) { Write-Error "pyinstaller install failed"; exit 1 }

# --- Step 1.5: Generate frame-sequence material ---
Write-Host "`n[1.5/4] Generate frameseq (shenshen)" -ForegroundColor Yellow
uv run python tools/convert_frameseq.py --character shenshen --include random,events
if ($LASTEXITCODE -ne 0) { Write-Error "frameseq generation failed"; exit 1 }

# --- Step 2: PyInstaller onedir build ---
Write-Host "`n[2/4] PyInstaller onedir (webm-chat)" -ForegroundColor Yellow
# Put uv venv Python first so build_onedir.ps1 uses it (not system Python)
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
powershell -ExecutionPolicy Bypass -File scripts\build_onedir.ps1 -Variant webm-chat
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller build failed"; exit 1 }

# --- Step 3: Verify onedir output ---
$onedir = "dist-onedir\dsh-pet-standalone-webm-chat"
if (-not (Test-Path "$onedir\dsh-pet-standalone-webm-chat.exe")) {
    Write-Error "onedir exe not found: $onedir"
    exit 1
}
Write-Host "`n[3/4] onedir OK: $onedir" -ForegroundColor Green

# --- Step 3.5: Rename exe + dir to product name ---
$oldExe = "$onedir\dsh-pet-standalone-webm-chat.exe"
$newExe = "$onedir\dsh-pet-chubby_blue_whale.exe"
if (Test-Path $oldExe) {
    Rename-Item $oldExe $newExe
    Write-Host "  Renamed exe -> dsh-pet-chubby_blue_whale.exe" -ForegroundColor Green
}
$newDir = "dist-onedir\dsh-pet-chubby_blue_whale"
if (Test-Path $onedir) {
    Rename-Item $onedir $newDir
    Write-Host "  Renamed dir -> dsh-pet-chubby_blue_whale" -ForegroundColor Green
}

# --- Step 4: Inno Setup compiler ---
Write-Host "`n[4/4] Inno Setup ISCC" -ForegroundColor Yellow
if (-not (Test-Path $ISCC)) {
    Write-Error "ISCC not found: $ISCC"
    Write-Host "Please install Inno Setup 7 or update `$ISCC path in this script." -ForegroundColor Red
    exit 1
}
& $ISCC "packaging\dsh-pet-chubby_blue_whale.iss"
if ($LASTEXITCODE -ne 0) { Write-Error "ISCC failed"; exit 1 }

# --- Done ---
$installer = "dist-onedir\dsh-pet-chubby_blue_whale-setup.exe"
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  BUILD COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installer: $installer" -ForegroundColor White
Write-Host "  Portable:  dist-onedir\dsh-pet-standalone-webm-chat-portable.zip" -ForegroundColor White
Write-Host ""