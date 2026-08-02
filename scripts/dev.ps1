param(
    [ValidateSet(
        "help", "start", "stop", "restart", "status", "logs", "test", "install",
        "db-migrate", "db-seed", "data-import", "data-import-review", "review-import"
    )]
    [string]$Action = "help"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendRoot = Join-Path $ProjectRoot "backend"
$FrontendRoot = Join-Path $ProjectRoot "frontend"
$RuntimeRoot = Join-Path $ProjectRoot ".runtime"
$BackendPidFile = Join-Path $RuntimeRoot "backend.pid"
$FrontendPidFile = Join-Path $RuntimeRoot "frontend.pid"
$BackendOutLog = Join-Path $RuntimeRoot "backend.out.log"
$BackendErrLog = Join-Path $RuntimeRoot "backend.err.log"
$FrontendOutLog = Join-Path $RuntimeRoot "frontend.out.log"
$FrontendErrLog = Join-Path $RuntimeRoot "frontend.err.log"
$BackendUrl = "http://127.0.0.1:8000"
$FrontendUrl = "http://127.0.0.1:5173"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-Http([string]$Url) {
    try {
        $null = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return $true
    }
    catch {
        return $false
    }
}

function Wait-Http([string]$Url, [string]$Name, [int]$TimeoutSeconds = 30) {
    for ($attempt = 0; $attempt -lt $TimeoutSeconds; $attempt++) {
        if (Test-Http $Url) {
            Write-Host "[OK] $Name" -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 1
    }
    throw "$Name did not start within $TimeoutSeconds seconds. Run make logs for details."
}

function Test-Port([int]$Port) {
    return $null -ne (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
}

function Test-Docker {
    & cmd.exe /d /c "docker info >nul 2>&1"
    return $LASTEXITCODE -eq 0
}

function Get-PortOwner([int]$Port) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $listener) {
        return $null
    }
    return $listener.OwningProcess
}

function Ensure-RuntimeDirectory {
    if (-not (Test-Path -LiteralPath $RuntimeRoot)) {
        $null = New-Item -ItemType Directory -Path $RuntimeRoot
    }
}

function Test-DependencyStamp([string]$SourceFile, [string]$StampFile) {
    if (-not (Test-Path -LiteralPath $StampFile)) {
        return $false
    }
    $expected = (Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash
    $actual = (Get-Content -LiteralPath $StampFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    return $expected -eq $actual
}

function Save-DependencyStamp([string]$SourceFile, [string]$StampFile) {
    $hash = (Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash
    Set-Content -LiteralPath $StampFile -Value $hash
}

function Ensure-Docker {
    if (Test-Docker) {
        return
    }

    $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path -LiteralPath $dockerDesktop)) {
        throw "Docker Desktop was not found. Install Docker Desktop first."
    }

    Write-Step "Starting Docker Desktop"
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        Start-Sleep -Seconds 2
        if (Test-Docker) {
            Write-Host "[OK] Docker Desktop" -ForegroundColor Green
            return
        }
    }
    throw "Docker Desktop did not become ready within 120 seconds."
}

function Ensure-Dependencies {
    $python = Join-Path $BackendRoot ".venv\Scripts\python.exe"
    $backendSource = Join-Path $BackendRoot "pyproject.toml"
    $backendStamp = Join-Path $RuntimeRoot "backend-deps.sha256"
    if (-not (Test-Path -LiteralPath $python)) {
        Write-Step "Installing backend dependencies"
        & python -m venv (Join-Path $BackendRoot ".venv")
        if ($LASTEXITCODE -ne 0) { throw "Failed to create the Python virtual environment." }
    }

    if (-not (Test-DependencyStamp $backendSource $backendStamp)) {
        Write-Step "Updating backend dependencies"
        Push-Location $BackendRoot
        try {
            & $python -m pip install -e ".[dev]"
            if ($LASTEXITCODE -ne 0) { throw "Failed to install backend dependencies." }
            Save-DependencyStamp $backendSource $backendStamp
        }
        finally {
            Pop-Location
        }
    }

    $frontendSource = Join-Path $FrontendRoot "package-lock.json"
    $frontendStamp = Join-Path $RuntimeRoot "frontend-deps.sha256"
    if ((-not (Test-Path -LiteralPath (Join-Path $FrontendRoot "node_modules"))) -or
        (-not (Test-DependencyStamp $frontendSource $frontendStamp))) {
        Write-Step "Installing frontend dependencies"
        Push-Location $FrontendRoot
        try {
            & npm.cmd install
            if ($LASTEXITCODE -ne 0) { throw "Failed to install frontend dependencies." }
            Save-DependencyStamp $frontendSource $frontendStamp
        }
        finally {
            Pop-Location
        }
    }
}

function Wait-ContainerHealth([string]$Service, [int]$TimeoutSeconds = 120) {
    for ($attempt = 0; $attempt -lt $TimeoutSeconds; $attempt++) {
        $containerId = (& docker compose ps -q $Service).Trim()
        if ($containerId) {
            $health = (& docker inspect --format "{{.State.Health.Status}}" $containerId 2>$null).Trim()
            if ($health -eq "healthy") {
                Write-Host "[OK] $Service" -ForegroundColor Green
                return
            }
            if ($health -eq "unhealthy") {
                throw "$Service failed its health check. Run make logs for details."
            }
        }
        Start-Sleep -Seconds 1
    }
    throw "$Service did not become ready within $TimeoutSeconds seconds."
}

function Start-Infrastructure {
    Ensure-Docker
    Write-Step "Starting MySQL and Redis"
    Push-Location $ProjectRoot
    try {
        & docker compose up -d mysql redis
        if ($LASTEXITCODE -ne 0) { throw "MySQL or Redis failed to start." }
        Wait-ContainerHealth "mysql"
        Wait-ContainerHealth "redis"
    }
    finally {
        Pop-Location
    }
}

function Invoke-DatabaseMigration {
    $alembic = Join-Path $BackendRoot ".venv\Scripts\alembic.exe"
    Write-Step "Applying database migrations"
    Push-Location $BackendRoot
    try {
        & $alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw "Database migration failed." }
    }
    finally {
        Pop-Location
    }
}

function Invoke-DemoDataSeed {
    $python = Join-Path $BackendRoot ".venv\Scripts\python.exe"
    Write-Step "Loading idempotent demo data"
    Push-Location $BackendRoot
    try {
        & $python -m app.db.seed
        if ($LASTEXITCODE -ne 0) { throw "Demo data initialization failed." }
    }
    finally {
        Pop-Location
    }
}

function Invoke-DemoPlatformImport {
    $python = Join-Path $BackendRoot ".venv\Scripts\python.exe"
    $fixture = Join-Path $BackendRoot "fixtures\ingestion\tujia-demo.json"
    Write-Step "Importing normalized demo platform data"
    Push-Location $BackendRoot
    try {
        & $python -m app.modules.ingestion.cli --platform tujia --fixture $fixture
        if ($LASTEXITCODE -ne 0) { throw "Demo platform data import failed." }
    }
    finally {
        Pop-Location
    }
}

function Invoke-DemoReviewImport {
    $python = Join-Path $BackendRoot ".venv\Scripts\python.exe"
    $fixture = Join-Path $BackendRoot "fixtures\reviews-demo.json"
    Write-Step "Importing and analyzing normalized demo reviews"
    Push-Location $BackendRoot
    try {
        & $python -m app.modules.review_analysis.cli --fixture $fixture
        if ($LASTEXITCODE -ne 0) { throw "Demo review import failed." }
    }
    finally {
        Pop-Location
    }
}

function Invoke-ReviewQueueDemoImport {
    $python = Join-Path $BackendRoot ".venv\Scripts\python.exe"
    $fixture = Join-Path $BackendRoot "fixtures\ingestion\review-required-demo.json"
    Write-Step "Importing a review-required listing demo"
    Push-Location $BackendRoot
    try {
        & $python -m app.modules.ingestion.cli --platform tujia --fixture $fixture
        if ($LASTEXITCODE -ne 0) { throw "Review queue demo import failed." }
    }
    finally {
        Pop-Location
    }
}

function Stop-RecordedProcess([string]$PidFile, [string]$ExpectedText, [string]$Name) {
    if (-not (Test-Path -LiteralPath $PidFile)) {
        return
    }

    $savedPid = Get-Content -LiteralPath $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not ($savedPid -as [int])) {
        Remove-Item -LiteralPath $PidFile -Force
        return
    }

    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $savedPid" -ErrorAction SilentlyContinue
    if ($null -eq $processInfo) {
        Remove-Item -LiteralPath $PidFile -Force
        return
    }

    if ($processInfo.CommandLine -notlike "*$ExpectedText*") {
        Write-Warning "$Name PID belongs to another process and was not stopped."
        Remove-Item -LiteralPath $PidFile -Force
        return
    }

    Stop-Process -Id ([int]$savedPid) -Force
    Remove-Item -LiteralPath $PidFile -Force
    Write-Host "[STOPPED] $Name"
}

function Clear-StaleRecordedProcess(
    [string]$PidFile,
    [string]$ExpectedText,
    [string]$Name,
    [string]$HealthUrl
) {
    if (Test-Http $HealthUrl) {
        return $true
    }
    Stop-RecordedProcess $PidFile $ExpectedText $Name
    return $false
}

function Assert-PortAvailable([int]$Port, [string]$Name) {
    if (Test-Port $Port) {
        $ownerPid = Get-PortOwner $Port
        throw "$Name port $Port is already used by process $ownerPid."
    }
}

function Start-Backend {
    if (Clear-StaleRecordedProcess $BackendPidFile "uvicorn" "FastAPI" "$BackendUrl/api/v1/health/live") {
        Write-Host "[RUNNING] FastAPI" -ForegroundColor Green
        return
    }

    Assert-PortAvailable 8000 "FastAPI"
    $python = Join-Path $BackendRoot ".venv\Scripts\python.exe"
    $process = Start-Process `
        -FilePath $python `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $BackendRoot `
        -RedirectStandardOutput $BackendOutLog `
        -RedirectStandardError $BackendErrLog `
        -WindowStyle Hidden `
        -PassThru
    Set-Content -LiteralPath $BackendPidFile -Value $process.Id
    Wait-Http "$BackendUrl/api/v1/health/live" "FastAPI"
}

function Start-Frontend {
    if (Clear-StaleRecordedProcess $FrontendPidFile "vite" "Vue frontend" $FrontendUrl) {
        Write-Host "[RUNNING] Vue frontend" -ForegroundColor Green
        return
    }

    Assert-PortAvailable 5173 "Vue frontend"
    $node = (Get-Command node.exe -ErrorAction Stop).Source
    $vite = Join-Path $FrontendRoot "node_modules\vite\bin\vite.js"
    $process = Start-Process `
        -FilePath $node `
        -ArgumentList @($vite) `
        -WorkingDirectory $FrontendRoot `
        -RedirectStandardOutput $FrontendOutLog `
        -RedirectStandardError $FrontendErrLog `
        -WindowStyle Hidden `
        -PassThru
    Set-Content -LiteralPath $FrontendPidFile -Value $process.Id
    Wait-Http $FrontendUrl "Vue frontend"
}

function Start-All {
    Ensure-RuntimeDirectory
    Ensure-Dependencies
    Start-Infrastructure
    Invoke-DatabaseMigration
    Invoke-DemoDataSeed
    Write-Step "Starting FastAPI and Vue"
    Start-Backend
    Start-Frontend
    Wait-Http "$BackendUrl/api/v1/health/ready" "FastAPI dependencies" 30

    Write-Host "`nStay Scale is running." -ForegroundColor Green
    Write-Host "Frontend: $FrontendUrl"
    Write-Host "API docs: $BackendUrl/docs"
    Write-Host "Health: $BackendUrl/api/v1/health/ready"
    Write-Host "`nRun make status for status or make stop to stop all services."
}

function Stop-All {
    Write-Step "Stopping frontend and backend"
    Stop-RecordedProcess $FrontendPidFile "vite" "Vue frontend"
    Stop-RecordedProcess $BackendPidFile "uvicorn" "FastAPI"

    if (Test-Docker) {
        Write-Step "Stopping MySQL and Redis"
        Push-Location $ProjectRoot
        try {
            & docker compose stop mysql redis
        }
        finally {
            Pop-Location
        }
    }
    Write-Host "`nStay Scale is stopped. Database volumes are preserved." -ForegroundColor Green
}

function Show-Status {
    Write-Host "Stay Scale status`n" -ForegroundColor Cyan
    Write-Host ("Vue frontend: " + $(if (Test-Http $FrontendUrl) { "running" } else { "stopped" }))
    Write-Host ("FastAPI:      " + $(if (Test-Http "$BackendUrl/api/v1/health/live") { "running" } else { "stopped" }))

    if (Test-Docker) {
        Push-Location $ProjectRoot
        try {
            & docker compose ps -a
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "Docker:       stopped"
    }
}

function Show-Logs {
    foreach ($log in @($BackendOutLog, $BackendErrLog, $FrontendOutLog, $FrontendErrLog)) {
        Write-Host "`n--- $([IO.Path]::GetFileName($log)) ---" -ForegroundColor Cyan
        if (Test-Path -LiteralPath $log) {
            Get-Content -LiteralPath $log -Tail 40
        }
        else {
            Write-Host "No logs yet."
        }
    }

    if (Test-Docker) {
        Write-Host "`n--- Docker ---" -ForegroundColor Cyan
        Push-Location $ProjectRoot
        try {
            & docker compose logs --tail 40 mysql redis
        }
        finally {
            Pop-Location
        }
    }
}

function Install-Dependencies {
    Ensure-RuntimeDirectory
    Ensure-Dependencies
    Write-Host "Dependencies are ready." -ForegroundColor Green
}

function Run-Tests {
    Ensure-Dependencies
    Write-Step "Backend tests and checks"
    $python = Join-Path $BackendRoot ".venv\Scripts\python.exe"
    Push-Location $BackendRoot
    try {
        & $python -m ruff format --check .
        if ($LASTEXITCODE -ne 0) { throw "Backend format check failed." }
        & $python -m ruff check .
        if ($LASTEXITCODE -ne 0) { throw "Backend lint failed." }
        & $python -m pytest
        if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }
    }
    finally {
        Pop-Location
    }

    Write-Step "Frontend tests and build"
    Push-Location $FrontendRoot
    try {
        & npm.cmd test
        if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed." }
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
    }
    finally {
        Pop-Location
    }
}

function Show-Help {
    Write-Host "Stay Scale development commands`n" -ForegroundColor Cyan
    Write-Host "make start    Start Docker, MySQL, Redis, FastAPI, and Vue"
    Write-Host "make stop     Stop all services and preserve database data"
    Write-Host "make restart  Restart all services"
    Write-Host "make status   Show service status"
    Write-Host "make logs     Show recent logs"
    Write-Host "make test     Run backend and frontend checks"
    Write-Host "make install  Install missing dependencies"
    Write-Host "make db-migrate  Apply pending MySQL migrations"
    Write-Host "make db-seed     Load or refresh demo data"
    Write-Host "make data-import Import and match the demo platform fixture"
    Write-Host "make review-import Import and analyze the demo review fixture"
    Write-Host "make data-import-review Create a review-required listing demo"
    Write-Host "`nWithout make, run .\start-dev.cmd or .\stop-dev.cmd."
}

Set-Location $ProjectRoot

switch ($Action) {
    "start" { Start-All }
    "stop" { Stop-All }
    "restart" { Stop-All; Start-All }
    "status" { Show-Status }
    "logs" { Show-Logs }
    "test" { Run-Tests }
    "install" { Install-Dependencies }
    "db-migrate" { Ensure-RuntimeDirectory; Ensure-Dependencies; Start-Infrastructure; Invoke-DatabaseMigration }
    "db-seed" { Ensure-RuntimeDirectory; Ensure-Dependencies; Start-Infrastructure; Invoke-DatabaseMigration; Invoke-DemoDataSeed }
    "data-import" { Ensure-RuntimeDirectory; Ensure-Dependencies; Start-Infrastructure; Invoke-DatabaseMigration; Invoke-DemoPlatformImport }
    "review-import" { Ensure-RuntimeDirectory; Ensure-Dependencies; Start-Infrastructure; Invoke-DatabaseMigration; Invoke-DemoReviewImport }
    "data-import-review" { Ensure-RuntimeDirectory; Ensure-Dependencies; Start-Infrastructure; Invoke-DatabaseMigration; Invoke-ReviewQueueDemoImport }
    default { Show-Help }
}
