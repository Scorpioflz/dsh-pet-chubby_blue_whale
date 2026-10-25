# build_update.ps1 - Build update installer (no assets, smaller package)
# Usage: powershell -ExecutionPolicy Bypass -File scripts\build_update.ps1
#
# 产物：dsh-pet-chubby_blue_whale-update-setup.exe
# 特点：打包时不包含 assets/characters/（动画素材），安装时不覆盖已有素材
# 用途：日常代码更新，避免每次重打 ~400MB 素材

$ErrorActionPreference = "Stop"
$ISCC = "D:\Tool\Inno Setup 7\ISCC.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  dsh-pet-chubby_blue_whale UPDATE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# --- Step 1: Install dependencies ---
Write-Host "`n[1/4] uv sync --extra build" -ForegroundColor Yellow
uv sync --extra build
if ($LASTEXITCODE -ne 0) { Write-Error "uv sync failed"; exit 1 }

# --- Step 2: PyInstaller onedir build (skip assets) ---
Write-Host "`n[2/4] PyInstaller onedir (skip assets)" -ForegroundColor Yellow
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
powershell -ExecutionPolicy Bypass -File scripts\build_onedir.ps1 -SkipZip -SkipAssets
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller build failed"; exit 1 }

# --- Step 3: Verify ---
$onedir = "dist-onedir\dsh-pet-chubby_blue_whale"
if (-not (Test-Path "$onedir\dsh-pet-chubby_blue_whale.exe")) {
    Write-Error "onedir exe not found: $onedir"
    exit 1
}
Write-Host "`n[3/4] onedir OK: $onedir (no assets)" -ForegroundColor Green

# --- Step 4: Inno Setup compiler ---
Write-Host "`n[4/4] Inno Setup ISCC" -ForegroundColor Yellow
if (-not (Test-Path $ISCC)) {
    Write-Error "ISCC not found: $ISCC"
    exit 1
}
& $ISCC "packaging\dsh-pet-chubby_blue_whale.iss"
if ($LASTEXITCODE -ne 0) { Write-Error "ISCC failed"; exit 1 }

# --- Rename to update installer ---
$installer = "dist-onedir\dsh-pet-chubby_blue_whale-setup.exe"
$updateInstaller = "dist-onedir\dsh-pet-chubby_blue_whale-update-setup.exe"
if (Test-Path $installer) {
    Move-Item $installer $updateInstaller -Force
    $sizeMB = [math]::Round((Get-Item $updateInstaller).Length / 1MB, 1)
    Write-Host "`n  Update installer: $updateInstaller ($sizeMB MB)" -ForegroundColor Green
}

# --- Done ---
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  UPDATE BUILD COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Update installer: $updateInstaller" -ForegroundColor White
Write-Host "  (no assets, installs over existing - keeps your animations)" -ForegroundColor DarkGray
Write-Host ""