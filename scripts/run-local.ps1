# Start all Cloud Run services locally (development)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".venv")) {
    python -m venv .venv
    .\.venv\Scripts\pip install -e .
}

$env:PYTHONPATH = $root
$services = @(
    @{ Module = "cloud_run_services.ai_gateway.main"; Port = 8080 },
    @{ Module = "cloud_run_services.rag_service.main"; Port = 8081 },
    @{ Module = "cloud_run_services.agent_service.main"; Port = 8082 },
    @{ Module = "cloud_run_services.jira_service.main"; Port = 8083 },
    @{ Module = "cloud_run_services.confluence_service.main"; Port = 8084 },
    @{ Module = "cloud_run_services.github_service.main"; Port = 8085 },
    @{ Module = "cloud_run_services.reporting_service.main"; Port = 8086 }
)

Write-Host "Starting Enterprise AI Platform services..."
foreach ($svc in $services) {
    $port = $svc.Port
    $module = $svc.Module
    Start-Process -NoNewWindow -FilePath ".\.venv\Scripts\python" -ArgumentList "-m", "uvicorn", "${module}:app", "--host", "0.0.0.0", "--port", $port
    Write-Host "  Started $module on :$port"
}

Write-Host ""
Write-Host "AI Gateway:  http://localhost:8080"
Write-Host "Frontend UI: cd frontend-ui && npm run dev  -> http://localhost:3000"
