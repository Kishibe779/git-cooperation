$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = "D:\Anaconda3\envs\FFFOP\python.exe"
$port = 8000

if (-not (Test-Path $python)) {
  Write-Host "Python not found: $python" -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "Starting CareerPilot backend..." -ForegroundColor Green
Write-Host "Project: $projectRoot"
Write-Host ""

Set-Location $projectRoot
$env:PYTHONDONTWRITEBYTECODE = "1"

function Test-AppHealth($candidatePort) {
  try {
    $response = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$candidatePort/api/v1/health" -TimeoutSec 2
    return $response.StatusCode -eq 200 -and $response.Content -like '*"status":"ok"*'
  } catch {
    return $false
  }
}

if (Test-AppHealth $port) {
  Write-Host "CareerPilot is already running." -ForegroundColor Green
  Write-Host "Open: http://127.0.0.1:$port/?v=20260428-4" -ForegroundColor Cyan
  Write-Host ""
  Write-Host "Press any key to close this window. The existing backend will keep running."
  $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
  exit 0
}

while ((Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1)) {
  Write-Host "Port $port is busy, trying $($port + 1)..." -ForegroundColor Yellow
  $port += 1
}

Write-Host "URL:     http://127.0.0.1:$port/?v=20260428-4" -ForegroundColor Cyan
Write-Host ""
Write-Host "Keep this window open while using the app. Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

& $python -B -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port $port
