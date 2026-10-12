$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force -Path reports | Out-Null
    $timer = [Diagnostics.Stopwatch]::StartNew()
    # No password prompt, remote mutation, installation, or training launch.
    $remote = 'echo SSH_KEY_OK && hostname && nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv && cd /root/autodl-tmp/underwater-segmentation && test -x .venv/bin/python && test -f data/UIIS/annotations/train.json && test -f data/UIIS/annotations/val.json && echo PROJECT_FILES_OK && df -h /root/autodl-tmp'
    # Windows PowerShell 5 treats native stderr as an error record.
    $ErrorActionPreference = 'Continue'
    $output = @(& ssh -F ./ssh.config -o BatchMode=yes -o ConnectTimeout=15 -o ConnectionAttempts=1 -o ServerAliveInterval=10 -o ServerAliveCountMax=2 underwater-gpu $remote 2>&1)
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    $timer.Stop()
    $body = ($output | ForEach-Object { $_.ToString() }) -join "`n"
    $result = "Checked: $(Get-Date -Format o)`nElapsedSeconds: $($timer.Elapsed.TotalSeconds)`nExitCode: $code`n$body`n"
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'reports/server-check.txt'), $result, [Text.UTF8Encoding]::new($false))
    Write-Output $result
    if ($code -ne 0) {
        if ($body -match 'Load key .*Permission denied') {
            throw 'LOCAL_KEY_ACCESS_DENIED: request targeted key read permission; do not alter ACLs or reinstall server keys.'
        }
        throw 'SERVER_CHECK_FAILED: inspect reports/server-check.txt; do not treat every failure as an authentication failure.'
    }
    if ($body -notmatch 'PROJECT_FILES_OK') { throw 'Server response did not confirm project files.' }
    Write-Output 'SERVER_READY'
} finally {
    Pop-Location
}
