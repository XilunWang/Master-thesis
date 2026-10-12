$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force -Path '.local' | Out-Null
    & ssh -F './ssh.config' underwater-gpu
} finally {
    Pop-Location
}
