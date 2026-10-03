# ============================================================
#  AI Job Matching System - Live Demo Launcher
#  Starts the backend, serves the live demo page, seeds sample
#  jobs, and opens the browser. Built for the stakeholder demo.
#
#  HOW TO RUN:
#    Put this script in the SAME folder as job_matcher_live.html,
#    then right-click it and choose "Run with PowerShell", or run:
#      powershell -ExecutionPolicy Bypass -File .\start_demo.ps1
# ============================================================

# ---- Settings (edit these two if your setup differs) -------
$RepoPath = "C:\Users\tjaym\Documents\AI-Job-Matching-System"  # where the backend code lives
$DemoDir  = $PSScriptRoot                                       # folder this script is in (holds the demo page)
# ------------------------------------------------------------
if (-not $DemoDir) { $DemoDir = (Get-Location).Path }   # fallback if run outside a file
$DemoPage = "job_matcher_live.html"
$ApiPort  = 8000
$PagePort = 5174

Write-Host "AI Job Matching System - demo launcher" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $RepoPath "app\main.py"))) {
    Write-Host "Could not find the backend at $RepoPath" -ForegroundColor Red
    Write-Host "Edit the `$RepoPath line at the top of this script to point at your repo folder." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"; exit 1
}
if (-not (Test-Path (Join-Path $DemoDir $DemoPage))) {
    Write-Host "Could not find $DemoPage next to this script." -ForegroundColor Red
    Write-Host "Put start_demo.ps1 in the same folder as $DemoPage." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"; exit 1
}

# 1. Postgres password (used only to build DATABASE_URL for this run; not saved)
$pw = Read-Host "Enter your PostgreSQL 'postgres' password"
$DbUrl = "postgresql+psycopg2://postgres:$pw@localhost:5432/test_db"

# 2. Launch the backend in its own window (venv + DATABASE_URL + ensure tables + uvicorn)
$backendCmd = @"
Set-Location '$RepoPath'
if (Test-Path '.\.venv\Scripts\Activate.ps1') { . .\.venv\Scripts\Activate.ps1 }
`$env:DATABASE_URL = '$DbUrl'
python -c "from app.database import Base, engine; import app.db_models; Base.metadata.create_all(bind=engine); print('tables ready')"
Write-Host 'Backend running on http://127.0.0.1:$ApiPort  (leave this window open)' -ForegroundColor Green
uvicorn app.main:app --host 127.0.0.1 --port $ApiPort --reload
"@
Start-Process powershell -ArgumentList "-NoExit","-Command",$backendCmd | Out-Null

# 3. Launch the page server in its own window (serves the demo folder)
$pageCmd = @"
Set-Location '$DemoDir'
Write-Host 'Serving demo at http://localhost:$PagePort/$DemoPage  (leave this window open)' -ForegroundColor Green
python -m http.server $PagePort
"@
Start-Process powershell -ArgumentList "-NoExit","-Command",$pageCmd | Out-Null

# 4. Wait for the backend to answer
Write-Host "Waiting for the backend to start..." -ForegroundColor Yellow
$ok = $false
for ($i = 0; $i -lt 25; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$ApiPort/" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Milliseconds 800 }
}

# 5. Seed the sample jobs so the demo is ready to match immediately
if ($ok) {
    Write-Host "Backend is up. Seeding sample jobs..." -ForegroundColor Green
    $jobs = @(
        @{ job_id="job-be"; title="Backend Engineer";          company="Test Co";      required_skills=@("Python","FastAPI","PostgreSQL");             posting_date="2026-09-01" },
        @{ job_id="job-de"; title="Data Engineer";             company="DataWorks";    required_skills=@("Python","Spark","AWS","Kafka");              posting_date="2026-09-02" },
        @{ job_id="job-fs"; title="Full Stack Developer";      company="Webify";       required_skills=@("JavaScript","React","Node.js","PostgreSQL"); posting_date="2026-09-05" },
        @{ job_id="job-ml"; title="Machine Learning Engineer"; company="Insight AI";   required_skills=@("Python","TensorFlow","PyTorch","SQL");       posting_date="2026-09-07" },
        @{ job_id="job-fe"; title="Frontend Developer";        company="Pixel Labs";   required_skills=@("JavaScript","React","CSS","HTML");           posting_date="2026-09-09" },
        @{ job_id="job-do"; title="DevOps Engineer";           company="CloudOps";     required_skills=@("Docker","Kubernetes","AWS","Linux");         posting_date="2026-09-11" },
        @{ job_id="job-qa"; title="QA Automation Engineer";    company="QualityFirst"; required_skills=@("Python","Selenium","pytest");                posting_date="2026-09-12" },
        @{ job_id="job-mb"; title="Mobile Developer";          company="Appology";     required_skills=@("Swift","Kotlin","Java");                     posting_date="2026-09-14" }
    )
    $seeded = 0
    foreach ($j in $jobs) {
        try {
            Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$ApiPort/api/v1/jobs/" -ContentType "application/json" -Body ($j | ConvertTo-Json) | Out-Null
            $seeded++
        } catch { }
    }
    Write-Host "Seeded $seeded of $($jobs.Count) jobs." -ForegroundColor Green
} else {
    Write-Host "Backend did not respond in time. The page may show 'Not connected' until the backend window finishes starting." -ForegroundColor Yellow
}

# 6. Open the demo in the browser
Start-Sleep -Seconds 1
Start-Process "http://localhost:$PagePort/$DemoPage"

Write-Host ""
Write-Host "Launched. Two windows opened (backend + page server) - leave them running during the demo." -ForegroundColor Cyan
Write-Host "In the page, just click 'Find my matches' (jobs are already seeded)." -ForegroundColor Cyan
Write-Host "To stop everything, close those two windows." -ForegroundColor Cyan
Read-Host "Press Enter to close this launcher window"
