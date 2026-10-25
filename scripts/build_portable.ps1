# build_portable.ps1 - Build portable zip only (no installer exe)
# Usage: powershell -ExecutionPolicy Bypass -File scripts\build_portable.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  dsh-pet-chubby_blue_whale portable" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# --- Step 1: Install dependencies ---
Write-Host "`n[1/4] uv sync --extra build" -ForegroundColor Yellow
uv sync --extra build
if ($LASTEXITCODE -ne 0) { Write-Error "uv sync failed"; exit 1 }

# --- Step 1.5: Generate frame-sequence material ---
$frameseqDir = "assets\characters\shenshen\frameseq"
if (Test-Path $frameseqDir -PathType Container) {
    $clipCount = (Get-ChildItem $frameseqDir -Recurse -Directory -Filter "g*" | Measure-Object).Count
    if ($clipCount -gt 0) {
        Write-Host "`n[1.5/4] Frameseq already exists ($clipCount clips), skip" -ForegroundColor Green
    } else {
        Write-Host "`n[1.5/4] Generate frameseq (shenshen)" -ForegroundColor Yellow
        uv run python tools/convert_frameseq_progress.py --character shenshen --include random,events
        if ($LASTEXITCODE -ne 0) { Write-Error "frameseq generation failed"; exit 1 }
    }
} else {
    Write-Host "`n[1.5/4] Generate frameseq (shenshen)" -ForegroundColor Yellow
    uv run python tools/convert_frameseq_progress.py --character shenshen --include random,events
    if ($LASTEXITCODE -ne 0) { Write-Error "frameseq generation failed"; exit 1 }
}

# --- Step 2: PyInstaller onedir build ---
Write-Host "`n[2/4] PyInstaller onedir" -ForegroundColor Yellow
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
powershell -ExecutionPolicy Bypass -File scripts\build_onedir.ps1
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller build failed"; exit 1 }

# --- Step 3: Verify ---
$onedir = "dist-onedir\dsh-pet-chubby_blue_whale"
if (-not (Test-Path "$onedir\dsh-pet-chubby_blue_whale.exe")) {
    Write-Error "onedir exe not found: $onedir"
    exit 1
}
Write-Host "`n[3/4] onedir OK: $onedir" -ForegroundColor Green

# --- Step 4: Portable zip ---
$zip = "dist-onedir\dsh-pet-chubby_blue_whale-portable.zip"
Write-Host "`n[4/4] Portable zip: $zip" -ForegroundColor Green

# --- Done ---
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  PORTABLE BUILD COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Portable zip: $zip" -ForegroundColor White
Write-Host "  Onedir dir:   $onedir" -ForegroundColor White
Write-Host ""