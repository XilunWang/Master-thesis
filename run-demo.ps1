$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & powershell -ExecutionPolicy Bypass -File ./sync-code.ps1
    if ($LASTEXITCODE -ne 0) { throw 'Code sync failed; demo not started' }
    & ssh -F ./ssh.config -o BatchMode=yes underwater-gpu 'cd /root/autodl-tmp/underwater-segmentation && .venv/bin/python scripts/demo-mask2former.py'
    if ($LASTEXITCODE -ne 0) { throw 'Remote demo failed' }
    New-Item -ItemType Directory -Force reports | Out-Null
    & scp -F ./ssh.config -o BatchMode=yes -r underwater-gpu:/root/autodl-tmp/underwater-segmentation/reports/demo-mask2former ./reports/
    if ($LASTEXITCODE -ne 0) { throw 'Result download failed' }
    Write-Host 'Results: reports/demo-mask2former/prediction.jpg'
} finally {
    Pop-Location
}
