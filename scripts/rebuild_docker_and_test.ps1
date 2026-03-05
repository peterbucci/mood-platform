[CmdletBinding()]
param(
    [switch]$NoCache,
    [switch]$SkipBuild,
    [switch]$StopAfter,
    [switch]$SkipLint,
    [switch]$SkipFormatCheck,
    [string]$DatabaseUrl = "postgresql://mood:mood@postgres:5432/mood",
    [string[]]$LintFiles = @(
        "apps/backend/app/services/fitbit_api_client.py",
        "apps/backend/app/services/fitbit_data_client.py",
        "apps/backend/app/services/fitbit_feature_builder.py",
        "apps/backend/app/services/request_fulfillment_service.py",
        "apps/backend/app/worker.py",
        "apps/backend/tests/test_fitbit_data_client.py",
        "apps/backend/tests/test_fitbit_feature_builder.py",
        "apps/backend/tests/test_request_fulfillment_service.py",
        "apps/backend/tests/test_worker_iteration_e2e.py"
    ),
    [string[]]$Tests = @(
        "apps/backend/tests/test_fitbit_api_client.py",
        "apps/backend/tests/test_fitbit_data_client.py",
        "apps/backend/tests/test_fitbit_feature_builder.py",
        "apps/backend/tests/test_fitbit_webhook_ingestion_service.py",
        "apps/backend/tests/test_webhook_coalescer.py",
        "apps/backend/tests/test_worker_runtime.py",
        "apps/backend/tests/test_worker_health_server.py",
        "apps/backend/tests/test_request_fulfillment_service.py",
        "apps/backend/tests/test_worker_iteration_e2e.py"
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

function Convert-ToContainerPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $normalized = $Path.Replace("\", "/")
    if ($normalized.StartsWith("apps/backend/")) {
        return $normalized.Substring("apps/backend/".Length)
    }
    return $normalized
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
        [string[]]$Urls = @(
            "http://localhost:8000/health/live",
            "http://localhost:8000/health/ready"
        ),
        [int]$MaxAttempts = 60,
        [int]$DelaySeconds = 2
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        foreach ($url in $Urls) {
            try {
                $response = Invoke-WebRequest -UseBasicParsing -Uri $url -Method Get -TimeoutSec 3
                if ($response.StatusCode -eq 200) {
                    Write-Host "API is healthy at $url."
                    return
                }
            }
            catch {
                # Service may still be starting.
            }
        }

        Start-Sleep -Seconds $DelaySeconds
    }

    throw "Timed out waiting for API health endpoints: $($Urls -join ', ')."
}

function Join-QuotedArgs {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Values
    )

    return ($Values | ForEach-Object { "'$_'" }) -join " "
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
try {
    if (-not $SkipBuild) {
        Invoke-Step -Name "Building Docker images (api, worker)" -Action {
            $buildArgs = @("build")
            if ($NoCache) {
                $buildArgs += "--no-cache"
            }
            $buildArgs += @("api", "worker")

            & docker compose @buildArgs
            if ($LASTEXITCODE -ne 0) {
                throw "docker compose build failed."
            }
        }
    }

    Invoke-Step -Name "Starting Docker services (postgres, redis)" -Action {
        docker compose up -d postgres redis
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose up failed."
        }
    }

    Invoke-Step -Name "Waiting for Postgres readiness" -Action {
        Wait-ForPostgres
    }

    Invoke-Step -Name "Running database migrations" -Action {
        docker compose run --rm api python -m alembic -c alembic.ini upgrade head
        if ($LASTEXITCODE -ne 0) {
            throw "alembic upgrade head failed."
        }
    }

    Invoke-Step -Name "Starting app services (api, worker)" -Action {
        docker compose up -d api worker
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose up failed."
        }
    }

    Invoke-Step -Name "Waiting for API readiness" -Action {
        Wait-ForApi
    }

    Invoke-Step -Name "Running lint/format/tests inside Docker (api image)" -Action {
        $containerLintFiles = @($LintFiles | ForEach-Object { Convert-ToContainerPath -Path $_ })
        $containerTests = @($Tests | ForEach-Object { Convert-ToContainerPath -Path $_ })

        $lintArgs = Join-QuotedArgs -Values $containerLintFiles
        $testArgs = Join-QuotedArgs -Values $containerTests

        $commands = New-Object System.Collections.Generic.List[string]
        $commands.Add("python -m pip install --quiet pytest ruff")

        if (-not $SkipLint) {
            $commands.Add("ruff check $lintArgs")
        }

        if (-not $SkipFormatCheck) {
            # Normalize line endings/format in ephemeral container copy before enforcing check.
            $commands.Add("ruff format $lintArgs")
            $commands.Add("ruff format --check $lintArgs")
        }

        $commands.Add("python -m pytest $testArgs -q")
        $innerCommand = [string]::Join(" && ", $commands)

        Write-Host "DATABASE_URL for Docker test run: $DatabaseUrl"
        & docker compose run --rm -e "DATABASE_URL=$DatabaseUrl" api sh -lc $innerCommand
        if ($LASTEXITCODE -ne 0) {
            throw "Docker test run failed."
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
