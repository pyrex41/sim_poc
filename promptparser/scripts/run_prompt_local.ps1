param(
    [string]$Prompt,
    [string]$OpenAIKey,
    [string]$BaseUrl = "http://127.0.0.1:8080",
    [string]$RedisUrl = "memory://",
    [switch]$IncludeCost,
    [switch]$UseMockLLM
)

function Ensure-Venv {
    if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
        Write-Host "[setup] Creating Python 3.11 virtualenv..."
        py -3.11 -m venv .venv | Out-Null
    }
}

function Ensure-Requirements {
    Write-Host "[setup] Installing/refreshing dependencies..."
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip > $null
    & .\.venv\Scripts\pip.exe install -r requirements.txt > $null
}

function Resolve-OpenAIKey {
    param([string]$InlineKey)

    if ($InlineKey) {
        return $InlineKey
    }
    if ($env:OPENAI_API_KEY) {
        return $env:OPENAI_API_KEY
    }

    $envPath = Join-Path (Get-Location) ".env"
    if (Test-Path $envPath) {
        $line = (Get-Content $envPath | Where-Object { $_ -match '^\s*OPENAI_API_KEY\s*=' }) | Select-Object -First 1
        if ($line -match '^\s*OPENAI_API_KEY\s*=\s*(.+)$') {
            return $Matches[1].Trim('"', "'")
        }
    }

    throw "OPENAI_API_KEY not provided. Pass -OpenAIKey or export it in the shell."
}

function Wait-For-Port {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 15
    )

    $uri = [Uri]$Url
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $test = Test-NetConnection -ComputerName $uri.Host -Port $uri.Port -WarningAction SilentlyContinue
        if ($test.TcpTestSucceeded) {
            return
        }
        Start-Sleep -Seconds 1
    }
    throw "Timed out waiting for $Url to become available."
}

function Prompt-For-Text {
    param([string]$Provided)
    if ($Provided) {
        return $Provided
    }
    Write-Host "Enter prompt text (Ctrl+Z then Enter to finish):"
    $text = ""
    while ($true) {
        $line = Read-Host
        if ($null -eq $line) { break }
        $text += if ($text) {"`n$line"} else {$line}
    }
    return $text.Trim()
}

$ErrorActionPreference = "Stop"
Push-Location (Split-Path $MyInvocation.MyCommand.Path -Parent) | Out-Null
Set-Location ..

try {
    Ensure-Venv
    Ensure-Requirements

    $key = Resolve-OpenAIKey -InlineKey $OpenAIKey
    $promptText = Prompt-For-Text -Provided $Prompt
    if (-not $promptText) { throw "Prompt text cannot be empty." }

    $env:OPENAI_API_KEY = $key
    $env:REDIS_URL = $RedisUrl
    $env:RATE_LIMIT_PER_MINUTE = "600"
    $env:USE_MOCK_LLM = $UseMockLLM.IsPresent ? "true" : "false"

    $logOut = Join-Path (Get-Location) "uvicorn_prompt.out.log"
    $logErr = Join-Path (Get-Location) "uvicorn_prompt.err.log"
    foreach ($log in @($logOut, $logErr)) {
        if (Test-Path $log) { Remove-Item $log -Force }
    }

    Write-Host "[run] Starting FastAPI on $BaseUrl ..."
    if ($UseMockLLM) {
        Write-Host "[run] Mock LLM enabled (no external API calls)."
    }
    $python = ".\.venv\Scripts\python.exe"
    $uvicorn = ".\.venv\Scripts\uvicorn.exe"
    $uvicornProcess = Start-Process -FilePath $uvicorn `
        -ArgumentList "app.main:app","--host","0.0.0.0","--port",([Uri]$BaseUrl).Port `
        -RedirectStandardOutput $logOut -RedirectStandardError $logErr `
        -PassThru
    try {
        Wait-For-Port -Url $BaseUrl

        $argsList = @("scripts\prompt_cli.py", $promptText, "--base-url", $BaseUrl)
        if ($IncludeCost) { $argsList += "--include-cost" }

        Write-Host "[run] Sending prompt..."
        $cliOutput = & $python $argsList 2>&1
        $cliExit = $LASTEXITCODE
        Write-Host ""
        Write-Host "[results] Prompt:"
        Write-Host $promptText
        Write-Host ""
        Write-Host "[results] creative_direction response:"
        Write-Host $cliOutput

        if ($cliExit -ne 0) {
            Write-Host ""
            Write-Host "[results] CLI exited with code $cliExit. Tail of uvicorn logs:"
            if (Test-Path $logOut) {
                Write-Host "--- stdout ($logOut) ---"
                Get-Content $logOut -Tail 20
            }
            if (Test-Path $logErr) {
                Write-Host "--- stderr ($logErr) ---"
                Get-Content $logErr -Tail 20
            }
        }
    }
    finally {
        if ($uvicornProcess -and -not $uvicornProcess.HasExited) {
            Write-Host "[cleanup] Stopping FastAPI (PID $($uvicornProcess.Id))..."
            $uvicornProcess | Stop-Process -Force
        }
    }
}
finally {
    Pop-Location | Out-Null
    Write-Host "[done] Local prompt run complete."
}

