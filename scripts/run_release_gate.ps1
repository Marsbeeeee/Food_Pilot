Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$frontendDir = Join-Path $repoRoot "frontend"

if (-not (Test-Path $python)) {
    throw ".venv Python not found at $python"
}

Write-Host "[gate] backend tests: pytest backend/tests"
& $python -m pytest backend/tests

Write-Host "[gate] frontend tests: npm.cmd test"
Push-Location $frontendDir
try {
    npm.cmd test

    if ($env:DASHSCOPE_API_KEY) {
        Write-Host "[gate] live e2e: npm.cmd run test:e2e"
        npm.cmd run test:e2e
    } else {
        Write-Host "[gate] live e2e skipped: DASHSCOPE_API_KEY is not set."
    }
} finally {
    Pop-Location
}

Write-Host "[gate] all required checks passed."
