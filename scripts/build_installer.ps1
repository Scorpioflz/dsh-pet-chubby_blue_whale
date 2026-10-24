# build_installer.ps1 - Build installer exe only (no portable zip)
# Usage: powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1

$ErrorActionPreference = "Stop"
$ISCC = "D:\Tool\Inno Setup 7\ISCC.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  dsh-pet-chubby_blue_whale installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# --- Step 1: Install dependencies ---
Write-Host "`n[1/5] uv sync + pyinstaller" -ForegroundColor Yellow
uv sync
if ($LASTEXITCODE -ne 0) { Write-Error "uv sync failed"; exit 1 }
uv pip install pyinstaller packaging
if ($LASTEXITCODE -ne 0) { Write-Error "pyinstaller install failed"; exit 1 }

# --- Step 1.5: Generate frame-sequence material ---
$frameseqDir = "assets\characters\shenshen\frameseq"
if (Test-Path $frameseqDir -PathType Container) {
    $clipCount = (Get-ChildItem $frameseqDir -Recurse -Directory -Filter "g*" | Measure-Object).Count
    if ($clipCount -gt 0) {
        Write-Host "`n[1.5/5] Frameseq already exists ($clipCount clips), skip" -ForegroundColor Green
    } else {
        Write-Host "`n[1.5/5] Generate frameseq (shenshen)" -ForegroundColor Yellow
        uv run python tools/convert_frameseq_progress.py --character shenshen --include random,events
        if ($LASTEXITCODE -ne 0) { Write-Error "frameseq generation failed"; exit 1 }
    }
} else {
    Write-Host "`n[1.5/5] Generate frameseq (shenshen)" -ForegroundColor Yellow
    uv run python tools/convert_frameseq_progress.py --character shenshen --include random,events
    if ($LASTEXITCODE -ne 0) { Write-Error "frameseq generation failed"; exit 1 }
}

# --- Step 2: PyInstaller onedir build ---
Write-Host "`n[2/5] PyInstaller onedir (webm-chat)" -ForegroundColor Yellow
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
powershell -ExecutionPolicy Bypass -File scripts\build_onedir.ps1 -Variant webm-chat -SkipZip
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller build failed"; exit 1 }

# --- Step 3: Verify + Rename ---
$onedir = "dist-onedir\dsh-pet-standalone-webm-chat"
if (-not (Test-Path "$onedir\dsh-pet-standalone-webm-chat.exe")) {
    Write-Error "onedir exe not found: $onedir"
    exit 1
}
Write-Host "`n[3/5] onedir OK: $onedir" -ForegroundColor Green

$oldExe = "$onedir\dsh-pet-standalone-webm-chat.exe"
if (Test-Path $oldExe) {
    Rename-Item $oldExe "dsh-pet-chubby_blue_whale.exe"
    Write-Host "  Renamed exe -> dsh-pet-chubby_blue_whale.exe" -ForegroundColor Green
}
if (Test-Path $onedir) {
    Rename-Item $onedir "dsh-pet-chubby_blue_whale"
    Write-Host "  Renamed dir -> dsh-pet-chubby_blue_whale" -ForegroundColor Green
}

# --- Step 4: Inno Setup compiler ---
Write-Host "`n[4/5] Inno Setup ISCC" -ForegroundColor Yellow
if (-not (Test-Path $ISCC)) {
    Write-Error "ISCC not found: $ISCC"
    exit 1
}
& $ISCC "packaging\dsh-pet-chubby_blue_whale.iss"
if ($LASTEXITCODE -ne 0) { Write-Error "ISCC failed"; exit 1 }


# --- Done ---
$installer = "dist-onedir\dsh-pet-chubby_blue_whale-setup.exe"
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  INSTALLER BUILD COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installer: $installer" -ForegroundColor White
Write-Host ""