[CmdletBinding()]
param(
    [switch]$NoCache,
    [switch]$SkipBuild,
    [switch]$StopAfter,
    [string]$DatabaseUrl = "postgresql://mood:mood@localhost:5432/mood",
    [string[]]$Tests = @(
        "apps/backend/tests/test_webhook_coalescer.py",
        "apps/backend/tests/test_fitbit_webhook_ingestion_service.py",
        "apps/backend/tests/test_fitbit_webhook_endpoint.py",
        "apps/backend/tests/test_fitbit_webhook_ingestion.py"
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Name"
    & $Action
}

function Get-PythonExecutable {
    $venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $pythonCmd) {
        return "python"
    }

    throw "Python executable not found. Create .venv or ensure python is on PATH."
}

function Wait-ForPostgres {
    param(
        [int]$MaxAttempts = 30,
        [int]$DelaySeconds = 2
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            docker compose exec -T postgres pg_isready -U mood -d mood | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Postgres is ready."
                return
            }
        }
        catch {
            # Service may still be starting.
        }
        Start-Sleep -Seconds $DelaySeconds
    }

    throw "Timed out waiting for postgres to become ready."
}

function Wait-ForApi {
    param(
        [string]$Url = "http://localhost:8000/health/live",
        [int]$MaxAttempts = 30,
        [int]$DelaySeconds = 2
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 3
            if ($response.StatusCode -eq 200) {
                Write-Host "API is healthy."
                return
            }
        }
        catch {
            # Service may still be starting.
        }
        Start-Sleep -Seconds $DelaySeconds
    }

    throw "Timed out waiting for API health endpoint at $Url."
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
try {
    if (-not $SkipBuild) {
        Invoke-Step -Name "Building Docker images (api, worker)" -Action {
            if ($NoCache) {
                docker compose build --no-cache api worker
            }
            else {
                docker compose build api worker
            }

            if ($LASTEXITCODE -ne 0) {
                throw "docker compose build failed."
            }
        }
    }

    Invoke-Step -Name "Starting Docker services" -Action {
        docker compose up -d postgres redis api worker
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose up failed."
        }
    }

    Invoke-Step -Name "Waiting for service readiness" -Action {
        Wait-ForPostgres
        Wait-ForApi
    }

    Invoke-Step -Name "Running backend webhook/coalescer tests" -Action {
        $pythonExe = Get-PythonExecutable
        Write-Host "Using python executable: $pythonExe"
        Write-Host "DATABASE_URL for tests: $DatabaseUrl"

        $previousDatabaseUrl = $env:DATABASE_URL
        try {
            $env:DATABASE_URL = $DatabaseUrl
            & $pythonExe -m pytest @Tests -q
            if ($LASTEXITCODE -ne 0) {
                throw "pytest failed."
            }
        }
        finally {
            if ($null -eq $previousDatabaseUrl) {
                Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
            }
            else {
                $env:DATABASE_URL = $previousDatabaseUrl
            }
        }
    }

    Write-Host ""
    Write-Host "Rebuild + test workflow completed successfully."
}
finally {
    if ($StopAfter) {
        Write-Host ""
        Write-Host "==> Stopping Docker services (--StopAfter)"
        docker compose down --remove-orphans
    }
    Pop-Location
}
