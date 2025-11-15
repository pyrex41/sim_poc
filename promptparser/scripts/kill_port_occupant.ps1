Param(
    [int]$Port = 8080,
    [switch]$Kill = $false
)

$ErrorActionPreference = "Stop"

function Get-ProcessChain {
    param ([int]$ProcessId)

    $chain = @()
    $visited = @{}
    while ($ProcessId -and $ProcessId -ne 0 -and -not $visited.ContainsKey($ProcessId)) {
        $visited[$ProcessId] = $true
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
        if (-not $proc) {
            $proc = Get-WmiObject Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
        }
        if (-not $proc) {
            break
        }
        $chain += $proc
        if (-not $proc.ParentProcessId -or $proc.ParentProcessId -eq $ProcessId) {
            break
        }
        $ProcessId = $proc.ParentProcessId
    }
    return $chain
}

$connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $connections) {
    Write-Host "No listeners currently bound to port $Port."
    return
}

$index = 1
foreach ($conn in $connections) {
    $processId = $conn.OwningProcess
    Write-Host "Connection #$index - PID $processId (State: $($conn.State))"
    $chain = Get-ProcessChain -ProcessId $processId
    for ($i = 0; $i -lt $chain.Count; $i++) {
        $proc = $chain[$i]
        $indent = " " * 4 * $i
        $cmd = $proc.CommandLine
        if ($cmd.Length -gt 100) {
            $cmd = $cmd.Substring(0, 97) + "..."
        }
        Write-Host "$indent PID $($proc.ProcessId) - Parent $($proc.ParentProcessId) - $cmd"
    }
    if ($Kill -and $chain.Count -gt 0) {
        $root = $chain[-1]
        Write-Host "Killing root PID $($root.ProcessId) ($($root.CommandLine))..."
        try {
            Stop-Process -Id $root.ProcessId -Force -ErrorAction Stop
            Write-Host "Root process terminated."
        } catch {
            Write-Warning "Failed to kill PID $($root.ProcessId): $_"
        }
    }
    $index++
}

