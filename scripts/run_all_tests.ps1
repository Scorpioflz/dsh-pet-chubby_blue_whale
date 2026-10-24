# run_all_tests.ps1 - Run each test file individually with 30s timeout
# Usage: powershell -ExecutionPolicy Bypass -File scripts\run_all_tests.ps1

$env:QT_QPA_PLATFORM = "offscreen"
uv pip install pytest pytest-timeout 2>$null | Out-Null

$testFiles = Get-ChildItem tests\test_*.py | Sort-Object Name
$passed = 0
$failed = 0
$failedList = @()

Write-Host "===== Running $($testFiles.Count) test files =====" -ForegroundColor Cyan

foreach ($f in $testFiles) {
    $name = $f.BaseName
    Write-Host -NoNewline "$name ... "
    $output = uv run python -m pytest $f.FullName --tb=no -q --timeout=10 2>&1
    if ($LASTEXITCODE -eq 0) {

        Write-Host "PASS" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "FAIL" -ForegroundColor Red
        $failed++
        $failedList += $name
    }
}

Write-Host "`n===== SUMMARY =====" -ForegroundColor Cyan
Write-Host "Passed: $passed | Failed: $failed | Total: $($testFiles.Count)" -ForegroundColor White
if ($failedList.Count -gt 0) {
    Write-Host "`nFailed tests:" -ForegroundColor Red
    foreach ($n in $failedList) {
        Write-Host "  $n" -ForegroundColor Red
    }
}
Write-Host ""