Param(
    [string]$BaseUrl = "http://127.0.0.1:8080",
    [string]$RedisUrl = "memory://",
    [int]$RateLimitPerMinute = 600,
    [string]$OpenAIKey = "",
    [switch]$UseMockLLM = $true
)

$ErrorActionPreference = "Stop"

function Ensure-Venv {
    if (-not (Test-Path ".\.venv")) {
        Write-Host "Creating Python 3.11 virtual environment..."
        py -3.11 -m venv .venv
    }
}

function Ensure-OpenAIKey {
    param ([string]$KeyFromParam)

    if ($KeyFromParam) {
        $env:OPENAI_API_KEY = $KeyFromParam
        Write-Host "OPENAI_API_KEY provided via parameter (value hidden)."
        return
    }

    if ($env:OPENAI_API_KEY) {
        Write-Host "OPENAI_API_KEY already present in environment."
        return
    }

    $envFile = Join-Path (Get-Location) ".env"
    Write-Host "Attempting to load OPENAI_API_KEY from $envFile ..."
    if (Test-Path $envFile) {
        foreach ($line in Get-Content $envFile) {
            if ($line -match '^\s*OPENAI_API_KEY\s*=\s*(.+)$') {
                $env:OPENAI_API_KEY = $Matches[1].Trim().Trim('"', "'")
                break
            }
        }
    }

    if (-not $env:OPENAI_API_KEY) {
        throw "OPENAI_API_KEY environment variable is required before running the load test."
    }

    Write-Host "OPENAI_API_KEY loaded from .env (value hidden)."
}

function Invoke-InVenv {
    param ([string]$Command)
    powershell -NoProfile -ExecutionPolicy Bypass -Command ". .\.venv\Scripts\Activate.ps1; $Command"
}

function Get-PortFromBaseUrl {
    param ([string]$Url)
    try {
        $uri = [System.Uri]$Url
        if ($uri.Port -gt 0) { return $uri.Port }
    } catch {
        throw "Invalid BaseUrl '$Url'. Provide a valid URL like http://127.0.0.1:18080"
    }
    return 8080
}

function Start-Uvicorn {
    Write-Host "Starting FastAPI (uvicorn) on $BaseUrl ..."
    $port = Get-PortFromBaseUrl -Url $BaseUrl
    if ($UseMockLLM) {
        $env:USE_MOCK_LLM = "1"
        Write-Host "USE_MOCK_LLM=1 (mock provider enabled)."
    } else {
        $env:USE_MOCK_LLM = ""
        Ensure-OpenAIKey -KeyFromParam $OpenAIKey
    }

    $env:REDIS_URL = $RedisUrl
    $env:RATE_LIMIT_PER_MINUTE = $RateLimitPerMinute
    $global:ApiProcess = Start-Process `
        -FilePath ".\.venv\Scripts\uvicorn.exe" `
        -ArgumentList "app.main:app","--host","0.0.0.0","--port","$port" `
        -NoNewWindow `
        -PassThru
    Start-Sleep -Seconds 3
}

function Stop-Uvicorn {
    if ($global:ApiProcess -and -not $global:ApiProcess.HasExited) {
        Write-Host "Stopping FastAPI..."
        $global:ApiProcess.CloseMainWindow() | Out-Null
        Start-Sleep -Seconds 1
        if (-not $global:ApiProcess.HasExited) {
            $global:ApiProcess.Kill()
        }
    }
}

function Invoke-K6 {
    param ([string]$BaseUrl)

    $k6Cmd = Get-Command k6 -ErrorAction SilentlyContinue
    if ($k6Cmd) {
        Write-Host "k6 binary detected at $($k6Cmd.Source). Running natively..."
        $env:BASE_URL = $BaseUrl
        k6 run tests/load/load_test.js
        return
    }

    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCmd) {
        throw "k6 CLI not found and Docker is unavailable. Install either k6 or Docker to continue."
    }

    $dockerBaseUrl = $BaseUrl
    if ($BaseUrl -match "127\.0\.0\.1" -or $BaseUrl -match "localhost") {
        $dockerBaseUrl = $BaseUrl -replace "127\.0\.0\.1","host.docker.internal"
        $dockerBaseUrl = $dockerBaseUrl -replace "localhost","host.docker.internal"
    }

    Write-Host "k6 not installed locally. Falling back to Docker (grafana/k6) with BASE_URL=$dockerBaseUrl ..."
    $currentPath = Get-Location
    docker run --rm `
        -e BASE_URL=$dockerBaseUrl `
        -v "$($currentPath.Path):/app" `
        -w /app `
        grafana/k6 run tests/load/load_test.js
}

try {
    Push-Location (Split-Path $MyInvocation.MyCommand.Path -Parent) | Out-Null
    Set-Location ..

    Ensure-Venv
    Write-Host "Installing dependencies..."
    Invoke-InVenv "pip install --quiet -r requirements.txt; pip install --quiet -r requirements-dev.txt"

    Start-Uvicorn

    Write-Host "Running k6 load test..."
    Invoke-K6 -BaseUrl $BaseUrl
}
finally {
    Stop-Uvicorn
    Pop-Location | Out-Null
}

