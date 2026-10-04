# ============================================================
#  Verify the AI embedding model matches skills by MEANING
#  Integration Lead: Terrance Montgomery
#
#  Run this from the REPOSITORY ROOT (the folder that contains the
#  "app" folder and verify_embeddings.py):
#
#     powershell -ExecutionPolicy Bypass -File .\Verify-Embeddings.ps1
#
#  It installs the optional model the first time, then shows the model
#  matching skills that share no letters (PyTorch ~ Deep Learning,
#  Scrum ~ Agile) -- something the TF-IDF baseline scores at 0%.
#
#  To test the hosted-API backup instead (needs OPENAI_API_KEY set):
#     .\Verify-Embeddings.ps1 -Mode api
# ============================================================

param(
    [ValidateSet("local", "api")]
    [string]$Mode = "local"
)

$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path (Join-Path $here "app\matching.py"))) {
    Write-Host "Run this from the repository root (the folder containing 'app' and verify_embeddings.py)." -ForegroundColor Red
    exit 2
}

# Find Python
$py = $null
foreach ($cand in @("python", "py")) {
    try { & $cand --version 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $py = $cand; break } } catch {}
}
if (-not $py) { Write-Host "Python not found on PATH." -ForegroundColor Red; exit 2 }
Write-Host "Using Python: $py" -ForegroundColor Cyan

if ($Mode -eq "local") {
    Write-Host "Installing the optional embedding model (first time can take a few minutes)..." -ForegroundColor Cyan
    if (Test-Path (Join-Path $here "requirements-embeddings.txt")) {
        & $py -m pip install --quiet --disable-pip-version-check -r (Join-Path $here "requirements-embeddings.txt") 2>&1 | Out-Host
    } else {
        & $py -m pip install --quiet --disable-pip-version-check sentence-transformers 2>&1 | Out-Host
    }
}

$env:AJMS_EMBEDDINGS = $Mode
Write-Host ""
& $py (Join-Path $here "verify_embeddings.py") --mode $Mode
exit $LASTEXITCODE
