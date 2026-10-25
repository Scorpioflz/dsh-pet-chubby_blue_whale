# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    dsh-pet-chubby_blue_whale onedir build + portable zip packaging.

.DESCRIPTION
    Builds a PyInstaller --onedir package (no runtime extraction, no _MEI cache),
    output at dist-onedir\dsh-pet-chubby_blue_whale\ plus a portable zip.

    Encoding isolation (issue #26):
      PYTHONUTF8=1 + PYTHONIOENCODING=utf-8 so neither PyInstaller nor helper
      scripts decode UTF-8 sources/resources with a legacy codepage.

    Bundle slimming: scripts\slim_bundle.py removes statically-unreferenced
      modules/resources. -SkipSlim keeps the bundle untouched.

    Local OCR models: resources\rapidocr_models\ ships with every build.

    Examples:
      powershell -ExecutionPolicy Bypass -File scripts\build_onedir.ps1
      powershell -ExecutionPolicy Bypass -File scripts\build_onedir.ps1 -SkipZip
      powershell -ExecutionPolicy Bypass -File scripts\build_onedir.ps1 -SkipSlim
#>
param(
    [switch]$SkipBuild,
    [switch]$SkipZip,
    [switch]$SkipCheck,
    [switch]$SkipSlim
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$buildStamp = (Get-Date).ToUniversalTime().ToString('o')
Write-Host "[build] pet-runtime-2026-09-01.1 build_started=$buildStamp source=$root" -ForegroundColor DarkCyan

$name  = 'dsh-pet-chubby_blue_whale'
$entry = 'packaging\pet_entry.py'

$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

python scripts\verify_bundle_tts.py --environment
if ($LASTEXITCODE -ne 0) { throw '[tts] upgrade build dependencies with uv sync' }

# Bridge zero-dependency check
$bridgeManifest = Join-Path $root 'integrations\dsh-pet-bridge\package.json'
if (-not (Test-Path $bridgeManifest)) { throw "Bridge manifest missing: $bridgeManifest" }
$bridgeManifestJson = [System.IO.File]::ReadAllText($bridgeManifest, [System.Text.Encoding]::UTF8)
$bridgePackage = $bridgeManifestJson | ConvertFrom-Json
$bridgeDepNames = @()
foreach ($field in 'dependencies', 'peerDependencies', 'optionalDependencies') {
    $deps = $bridgePackage.$field
    if ($deps) { $bridgeDepNames += @($deps.PSObject.Properties | ForEach-Object { $_.Name }) }
}
if ($bridgeDepNames.Count -gt 0) {
    throw "[bridge] runtime dependencies are forbidden (zero-dependency red line): " +
          ($bridgeDepNames -join ', ') +
          " - hand-roll what you need inside index.js instead"
}
$nodeExe = Get-Command node -ErrorAction SilentlyContinue
if ($nodeExe) {
    $smoke = Join-Path $root 'integrations\dsh-pet-bridge\verify_import.mjs'
    if (-not (Test-Path $smoke)) { throw "missing verify script: $smoke" }
    Write-Host "[bridge] verifying zero-dependency plugin import (hermetic smoke)..." -ForegroundColor Cyan
    & node $smoke
    if ($LASTEXITCODE -ne 0) { throw "[bridge] plugin import smoke test failed (exit $LASTEXITCODE)" }
    Write-Host "[bridge] import smoke OK" -ForegroundColor Green
} else {
    Write-Host "[bridge] node not found - smoke skipped (PR gate covers it)" -ForegroundColor Yellow
}

$datas = 'assets/characters;assets/characters'
$excludes = @()
$excludes += @('--exclude-module', 'OpenGL')
foreach ($m in @('torch','transformers','datasets','langchain','langchain_core',
                 'langchain_openai','langsmith','langgraph','wandb','sentry_sdk',
                 'pandas','numba','llvmlite','pyarrow','polars','_polars_runtime_32',
                 'spacy','playwright','narwhals','sympy','fsspec')) {
    $excludes += @('--exclude-module', $m)
}
foreach ($m in @('PyQt5','PyQt6','PySide2')) {
    $excludes += @('--exclude-module', $m)
}
foreach ($m in @('matplotlib','matplotlib_inline','seaborn','IPython','ipykernel',
                 'jupyter_client','jupyter_core','nbformat','zmq')) {
    $excludes += @('--exclude-module', $m)
}
foreach ($m in @('django','hypothesis')) {
    $excludes += @('--exclude-module', $m)
}
$keyringCollect = @('--collect-all', 'keyring')
$keyringCollect += @('--collect-all', 'win32ctypes')
$chatData = @(
    '--add-data', 'pet\chat\legacy_styles.qss;pet\chat',
    '--add-data', 'pet\chat\modern_styles.qss;pet\chat'
)

# Stop running exe before build
$running = Get-Process -Name $name -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "[build] stopping running $name before build..." -ForegroundColor Yellow
    $running | Stop-Process -Force
    Start-Sleep -Milliseconds 800
}

if (-not $SkipBuild) {
    Write-Host "[0/3] Generating app icon..." -ForegroundColor Cyan
    python scripts\make_icon.py
    if ($LASTEXITCODE -ne 0) { throw "make_icon failed: $LASTEXITCODE" }

    Write-Host "[frameseq] verifying frame-sequence material completeness..." -ForegroundColor Cyan
    python scripts\check_frameseq_bundle.py
    if ($LASTEXITCODE -ne 0) { throw "check_frameseq_bundle failed: $LASTEXITCODE" }
    Write-Host "[frameseq] frame-sequence material OK" -ForegroundColor Green

    Write-Host "[presentmon] verifying bundled game-FPS capture backend..." -ForegroundColor Cyan
    python scripts\verify_presentmon.py
    if ($LASTEXITCODE -ne 0) { throw "verify_presentmon failed: $LASTEXITCODE" }
    Write-Host "[presentmon] capture backend OK" -ForegroundColor Green

    Write-Host "[rapidocr] verifying bundled local OCR models..." -ForegroundColor Cyan
    python scripts\verify_rapidocr_models.py
    if ($LASTEXITCODE -ne 0) { throw "verify_rapidocr_models failed: $LASTEXITCODE" }
    Write-Host "[rapidocr] local OCR models OK" -ForegroundColor Green

    $rapidocrDir = (& python -c "import os, rapidocr; print(os.path.dirname(rapidocr.__file__))").Trim()
    if (-not $rapidocrDir) { throw "[rapidocr] cannot resolve the rapidocr package directory" }
    foreach ($cfgName in @('config.yaml', 'default_models.yaml')) {
        if (-not (Test-Path (Join-Path $rapidocrDir $cfgName))) {
            throw "[rapidocr] package data missing in $rapidocrDir : $cfgName"
        }
    }
    $rapidocrData = @(
        '--add-data', 'resources\rapidocr_models;resources\rapidocr_models',
        '--add-data', "$rapidocrDir\config.yaml;rapidocr",
        '--add-data', "$rapidocrDir\default_models.yaml;rapidocr"
    )
    $rapidocrHidden = @(
        '--hidden-import', 'pet.screen_capture.ocr',
        '--hidden-import', 'pet.screen_capture.ocr_worker'
    )

    $env:PATH = ($env:PATH -split ';' | Where-Object {
    $_ -and $_ -notmatch '(?i)(conda|miniconda)[\\/].*[\\/]Library[\\/]bin$' -and
        $_ -notmatch '(?i)[\\/]envs[\\/].*[\\/]Library[\\/]bin$' -and
            $_ -notmatch '(?i)MiKTeX[\\/]miktex[\\/]bin'
    }) -join ';'

    Write-Host "[1/3] PyInstaller --onedir building $name ..." -ForegroundColor Cyan
    python -m PyInstaller --noconfirm --clean --onedir --windowed --noupx `
        --name $name `
        --distpath dist-onedir `
        --workpath build-onedir `
        --icon assets\icon.ico `
        --collect-all imageio_ffmpeg `
        --collect-all certifi `
        --collect-all PySide6.QtMultimedia `
        --collect-all edge_tts `
        --collect-all aiofiles `
        --collect-all tzdata `
        --collect-all psutil `
        @keyringCollect `
        --add-data $datas `
        --add-data "assets\big_blue_fat_fish;assets\big_blue_fat_fish" `
        --add-data "pet\persona_presets;pet\persona_presets" `
        --add-data "pet\menu_templates;pet\menu_templates" `
        @chatData `
        --add-data "assets\sounds;assets\sounds" `
        --add-data "assets\chat;assets\chat" `
        --add-data "assets\icon.ico;assets" `
        --add-data "LICENSE;." `
        --add-data "THIRD_PARTY_NOTICES.md;." `
        --add-data "integrations;integrations" `
        --add-data "resources\presentmon;resources\presentmon" `
        @rapidocrData `
        @rapidocrHidden `
        @excludes `
        $entry
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed: $LASTEXITCODE" }
}

$appDir = Join-Path $root "dist-onedir\$name"
if (-not (Test-Path $appDir)) { throw "Build output missing: $appDir" }

# Bridge zero-dependency enforcement
Write-Host "[bridge] enforcing zero-dependency bundle..." -ForegroundColor Cyan
python scripts\fix_bridge_bundle.py --app-dir $appDir
if ($LASTEXITCODE -ne 0) { throw "Bridge zero-dependency check failed: $LASTEXITCODE" }
Write-Host "[bridge] zero-dependency bundle OK" -ForegroundColor Green

# Qt runtime post-build
$pythonPrefix = (& python -c "import sys; print(sys.prefix)").Trim()
$condaBin = Join-Path $pythonPrefix "Library\bin"
$condaQtPlugins = Join-Path $pythonPrefix "Library\lib\qt6\plugins"
$bundlePySide = Join-Path $appDir "_internal\PySide6"
$bundleShiboken = Join-Path $appDir "_internal\shiboken6"

$qtNonSystemDeps = @(
    'MSVCP140.dll','MSVCP140_1.dll','MSVCP140_2.dll',
    'VCRUNTIME140.dll','VCRUNTIME140_1.dll',
    'double-conversion.dll','freetype.dll','libcrypto-3-x64.dll',
    'libpng16.dll','pcre2-16.dll','zlib.dll','zstd.dll',
    'icudt75.dll','icuin75.dll','icuuc75.dll'
)

Write-Host "[Qt] Python prefix: $pythonPrefix"

if (Test-Path (Join-Path $condaBin 'Qt6Core.dll')) {
    Write-Host "[Qt] Runtime source: $condaBin"
    Write-Host "[Qt] Copying runtime..."
    if (-not (Test-Path $bundlePySide)) { throw "[Qt] bundle PySide6 dir missing: $bundlePySide" }
    Get-ChildItem $condaBin -Filter 'Qt6*.dll' -ErrorAction SilentlyContinue | ForEach-Object {
        Copy-Item $_.FullName $bundlePySide -Force
    }
    foreach ($dep in $qtNonSystemDeps) {
        $depSrc = Join-Path $condaBin $dep
        if (Test-Path $depSrc) { Copy-Item $depSrc $bundlePySide -Force }
    }
    $shibokenDll = Join-Path $condaBin 'shiboken6.cp310-win_amd64.dll'
    if (Test-Path $shibokenDll) {
        Copy-Item $shibokenDll $bundleShiboken -Force
        Write-Host "[Qt] copied shiboken6.cp310-win_amd64.dll to shiboken6/"
    }
    $pyside6Dll = Join-Path $condaBin 'pyside6.cp310-win_amd64.dll'
    if (Test-Path $pyside6Dll) {
        Copy-Item $pyside6Dll $bundlePySide -Force
        Write-Host "[Qt] copied pyside6.cp310-win_amd64.dll to PySide6/"
    }
    Write-Host "[Qt] Copying plugins..."
    $dstPlatforms = Join-Path $bundlePySide 'plugins\platforms'
    if (-not (Test-Path (Join-Path $dstPlatforms 'qwindows.dll'))) {
        if (Test-Path (Join-Path $condaQtPlugins 'platforms')) {
            if (-not (Test-Path $dstPlatforms)) { New-Item -ItemType Directory -Path $dstPlatforms -Force | Out-Null }
            Copy-Item (Join-Path $condaQtPlugins 'platforms\*') $dstPlatforms -Force
            Write-Host "[Qt] copied platform plugins from $condaQtPlugins"
        } else {
            throw "[Qt] qwindows.dll missing and conda plugin dir not found: $condaQtPlugins"
        }
    }
    Write-Host "[Qt] Runtime validation OK" -ForegroundColor Green
    foreach ($dep in @('libcrypto-3-x64.dll', 'libssl-3-x64.dll')) {
        $depSrc = Join-Path $condaBin $dep
        $depDst = Join-Path $appDir "_internal\$dep"
        if (Test-Path $depSrc) {
            Copy-Item $depSrc $depDst -Force
            Write-Host "[SSL] copied $dep to bundle _internal/"
        }
    }
} else {
    Write-Host "[Qt] pip PySide6 (Qt6 DLL bundled), runtime copy skipped" -ForegroundColor Yellow
}

# Qt runtime validation
$qtRequired = @('Qt6Core.dll','Qt6Gui.dll','Qt6Widgets.dll','plugins\platforms\qwindows.dll')
foreach ($rel in $qtRequired) {
    $full = Join-Path $bundlePySide $rel
    if (-not (Test-Path $full)) { throw "[Qt] required file missing in bundle: $rel" }
}
if (Test-Path (Join-Path $condaBin 'Qt6Core.dll')) {
    foreach ($dep in $qtNonSystemDeps) {
        if (-not (Test-Path (Join-Path $bundlePySide $dep))) {
            throw "[Qt] conda Qt dependency missing in bundle: $dep"
        }
    }
    if (-not (Test-Path (Join-Path $bundleShiboken 'shiboken6.cp310-win_amd64.dll'))) {
        throw "[Qt] shiboken6.cp310-win_amd64.dll missing in bundle shiboken6/"
    }
    if (-not (Test-Path (Join-Path $bundlePySide 'pyside6.cp310-win_amd64.dll'))) {
        throw "[Qt] pyside6.cp310-win_amd64.dll missing in bundle PySide6/"
    }
}
Write-Host "[Qt] Runtime validation OK" -ForegroundColor Green

# DLL conflict check
$allowedIcu = @('icuuc.dll', 'icudt78.dll')
$badIcu = Get-ChildItem -Recurse -Path $appDir -Filter 'icu*.dll' -ErrorAction SilentlyContinue |
    Where-Object {
        if ($_.DirectoryName -like '*\_internal\PySide6') { return $false }
        $version = $_.VersionInfo.FileVersion
        -not ($allowedIcu -contains $_.Name -and $version -like '78, 3, 0, 0*')
    }
$badQt = Get-ChildItem -Recurse -Path $appDir -Filter 'Qt6*.dll' -ErrorAction SilentlyContinue |
    Where-Object {
        $_.DirectoryName -notlike '*\_internal' -and
            $_.DirectoryName -notlike '*\PySide6*' -and
            $_.DirectoryName -notlike '*\shiboken6*'
    }
if ($badIcu -or $badQt) {
    $names = @($badIcu.Name) + @($badQt.Name)
    throw "Bundle contains incompatible Qt/ICU DLLs ($($names -join ', '))."
}

# Bundle slimming
if (-not $SkipSlim) {
    Write-Host "[1.5/3] Slimming bundle (unused Qt modules / redundant resources)..." -ForegroundColor Cyan
    python scripts\slim_bundle.py --app-dir $appDir
    if ($LASTEXITCODE -ne 0) { throw "Bundle slimming failed: $LASTEXITCODE" }
    Write-Host "[slim] bundle slimmed" -ForegroundColor Green
}

# Encoding check
if (-not $SkipCheck) {
    Write-Host "[1.6/3] Chinese-encoding self-check on bundle..." -ForegroundColor Cyan
    python scripts\check_bundle_encoding.py --dir $appDir
    if ($LASTEXITCODE -ne 0) {
        throw "Bundle encoding check failed - refusing to package garbled output (issue #26)"
    }
}

# Smoke window wait function
function Wait-SmokeWindow {
    param(
        [Parameter(Mandatory = $true)][System.Diagnostics.Process]$Process,
        [Parameter(Mandatory = $true)][string]$Label,
        [string]$EarlyExitHint = 'runtime dependency broken',
        [string]$NoWindowHint = "startup failed (likely 'Failed to execute script')",
        [int]$TimeoutSec = 90
    )
    $t0 = Get-Date
    $deadline = $t0.AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 250
        if ($Process.HasExited) {
            throw "[smoke] $Label exited early (code $($Process.ExitCode)) - $EarlyExitHint"
        }
        $Process.Refresh()
        if ($Process.MainWindowHandle -ne 0) {
            $elapsed = ((Get-Date) - $t0).TotalSeconds
            Write-Host ("[smoke] $Label window appeared after {0:N1}s" -f $elapsed) -ForegroundColor DarkGray
            return
        }
    }
    throw "[smoke] $Label running but no window appeared within ${TimeoutSec}s - $NoWindowHint"
}

# PresentMon bundle verification
$backendName = (& python -c "from pet.island import game_fps; print(game_fps.BACKEND_EXE_NAME)").Trim()
if (-not $backendName) { throw "[presentmon] cannot resolve BACKEND_EXE_NAME from pet/game_fps.py" }
$backendInBundle = Join-Path $appDir ("_internal\resources\presentmon\" + $backendName)
Write-Host "[presentmon] verifying bundled backend in the built app..." -ForegroundColor Cyan
python scripts\verify_presentmon.py --path $backendInBundle
if ($LASTEXITCODE -ne 0) { throw "[presentmon] bundled capture backend missing or corrupt" }
Write-Host "[presentmon] bundle carries the capture backend + its license" -ForegroundColor Green

# OCR bundle verification
Write-Host "[rapidocr] verifying the built app carries the engine module + models..." -ForegroundColor Cyan
python scripts\verify_rapidocr_models.py --app-dir $appDir
if ($LASTEXITCODE -ne 0) { throw "[rapidocr] bundle cannot run local OCR (module missing or models corrupt)" }
Write-Host "[rapidocr] bundle carries the engine module + models + rapidocr config" -ForegroundColor Green

# TTS bundle verification
python scripts\verify_bundle_tts.py --app-dir $appDir
if ($LASTEXITCODE -ne 0) { throw '[tts] bundled dependency version or modules are invalid' }

# exe smoke test
$exePath = Join-Path $appDir "$name.exe"
if (-not (Test-Path $exePath)) { throw "Build exe missing: $exePath" }

$verifyScript = Join-Path $root 'scripts\verify_bundle_qt.py'
if (-not (Test-Path $verifyScript)) { throw "missing verify script: $verifyScript" }
Write-Host "[smoke] verifying bundle DLL chain (Shiboken/QtCore/QtGui/QtWidgets)..." -ForegroundColor Cyan
python $verifyScript --internal (Join-Path $appDir '_internal')
if ($LASTEXITCODE -ne 0) { throw "[smoke] bundle DLL chain verification failed" }
Write-Host "[smoke] bundle DLL chain OK" -ForegroundColor Green

Write-Host "[smoke] Launching $exePath ..." -ForegroundColor Cyan
$proc = Start-Process -FilePath $exePath -PassThru
try {
    Wait-SmokeWindow -Process $proc -Label 'exe'
} finally {
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}
Write-Host "[smoke] exe started OK" -ForegroundColor Green

# --settings smoke test
Write-Host "[smoke] Launching $exePath --settings ..." -ForegroundColor Cyan
$smokeBase = Join-Path $env:TEMP ("dsh-settings-smoke-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $smokeBase -Force | Out-Null
$oldAppData = $env:APPDATA
$env:APPDATA = $smokeBase
$settingsProc = $null
try {
    $settingsProc = Start-Process -FilePath $exePath -ArgumentList '--settings' -PassThru
    Wait-SmokeWindow -Process $settingsProc -Label '--settings' `
        -EarlyExitHint 'arg routing broken' `
        -NoWindowHint 'no settings window appeared'
    $settingsLock = Join-Path (Join-Path $smokeBase $name) 'settings.lock'
    if (-not (Test-Path $settingsLock)) {
        throw "[smoke] --settings did not acquire settings.lock"
    }
} finally {
    if ($settingsProc -and -not $settingsProc.HasExited) {
        Stop-Process -Id $settingsProc.Id -Force -ErrorAction SilentlyContinue
    }
    $env:APPDATA = $oldAppData
    Remove-Item $smokeBase -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "[smoke] --settings started OK" -ForegroundColor Green

if (-not $SkipZip) {
    Write-Host "[2/3] Packing portable zip..." -ForegroundColor Cyan
    $zip = Join-Path $root "dist-onedir\$name-portable.zip"
    Remove-Item $zip -Force -ErrorAction SilentlyContinue
    Compress-Archive -Path "$appDir\*" -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "      $zip ($([math]::Round((Get-Item $zip).Length/1MB,1)) MB)" -ForegroundColor Green
}

Write-Host "[3/3] Done. onedir dir: $appDir" -ForegroundColor Green
Write-Host "      Installer: compile packaging\dsh-pet-chubby_blue_whale.iss with ISCC.exe"
