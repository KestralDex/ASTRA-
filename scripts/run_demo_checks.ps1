$ErrorActionPreference = "Stop"

if (-not $env:VIRTUAL_ENV) {
    Write-Error "ASTRA .venv is not active. Activate it first with .\.venv\Scripts\Activate.ps1"
}

Write-Host ""
Write-Host "=== ASTRA October 1 Demo Hardening ===" -ForegroundColor Cyan
Write-Host ""

python scripts\demo_smoke_test.py

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Running full pytest suite..." -ForegroundColor Cyan
python -m pytest -q

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "ALL AUTOMATED CHECKS PASSED." -ForegroundColor Green
Write-Host "Now complete docs\demo_regression_checklist.md" -ForegroundColor Green
