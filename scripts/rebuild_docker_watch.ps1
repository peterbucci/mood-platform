[CmdletBinding()]
param(
    [switch]$NoCache,
    [switch]$Watch,
    [int]$PollSeconds = 2,
    [string[]]$WatchPaths = @(
        "apps/backend",
        "docker-compose.yml",
        ".env"
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Rebuild {
    param([switch]$NoCacheBuild)

    Write-Host ""
    Write-Host "==> Rebuilding Docker images"

    $buildArgs = @("compose", "build")
    if ($NoCacheBuild) {
        $buildArgs += "--no-cache"
    }
    $buildArgs += @("api", "worker")

    & docker @buildArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose build failed."
    }

    Write-Host ""
    Write-Host "==> Starting data services"
    docker compose up -d postgres redis
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up (postgres/redis) failed."
    }

    Write-Host ""
    Write-Host "==> Running database migrations"
    docker compose run --rm api python -m alembic -c alembic.ini upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "alembic upgrade head failed."
    }

    Write-Host ""
    Write-Host "==> Starting app services"
    docker compose up -d api worker
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up (api/worker) failed."
    }
}

function Get-WatchFingerprint {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Paths
    )

    $excludeDirPattern = [regex]"(\\|/)(\.git|\.venv|node_modules|__pycache__|\.pytest_cache|\.ruff_cache|dist|build)(\\|/|$)"
    $entries = New-Object System.Collections.Generic.List[string]

    foreach ($path in $Paths) {
        if (-not (Test-Path -LiteralPath $path)) {
            continue
        }

        $item = Get-Item -LiteralPath $path
        if ($item.PSIsContainer) {
            Get-ChildItem -LiteralPath $item.FullName -Recurse -File | Where-Object {
                -not $excludeDirPattern.IsMatch($_.FullName)
            } | ForEach-Object {
                $entries.Add("$($_.FullName)|$($_.LastWriteTimeUtc.Ticks)|$($_.Length)")
            }
        }
        else {
            $entries.Add("$($item.FullName)|$($item.LastWriteTimeUtc.Ticks)|$($item.Length)")
        }
    }

    $sorted = $entries | Sort-Object
    $joined = [string]::Join("`n", $sorted)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($joined)
        $hash = $sha.ComputeHash($bytes)
        return ([System.BitConverter]::ToString($hash)).Replace("-", "")
    }
    finally {
        $sha.Dispose()
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
try {
    Invoke-Rebuild -NoCacheBuild:$NoCache
    Write-Host ""
    Write-Host "Docker rebuild complete."

    if (-not $Watch) {
        Write-Host "Tip: use -Watch to auto-rebuild on file changes."
        return
    }

    Write-Host ""
    Write-Host "Watch mode enabled. Polling every $PollSeconds second(s). Press Ctrl+C to stop."
    $lastFingerprint = Get-WatchFingerprint -Paths $WatchPaths

    while ($true) {
        Start-Sleep -Seconds $PollSeconds
        $currentFingerprint = Get-WatchFingerprint -Paths $WatchPaths
        if ($currentFingerprint -eq $lastFingerprint) {
            continue
        }

        $lastFingerprint = $currentFingerprint
        Write-Host ""
        Write-Host "Change detected at $(Get-Date -Format "yyyy-MM-dd HH:mm:ss"). Rebuilding..."

        try {
            Invoke-Rebuild -NoCacheBuild:$NoCache
            Write-Host "Rebuild complete."
        }
        catch {
            Write-Host "Rebuild failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
finally {
    Pop-Location
}
