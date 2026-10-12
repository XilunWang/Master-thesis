$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    # Respect Git exclusions. Include new source files before their first commit.
    $sourceFiles = @(& git -c core.quotepath=false ls-files --cached --others --exclude-standard)
    if ($LASTEXITCODE -ne 0 -or $sourceFiles.Count -eq 0) { throw 'Cannot list project files' }
    $sourceFiles = @($sourceFiles | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
    $manifest = Join-Path $PSScriptRoot '.local/upload-files.txt'
    [System.IO.File]::WriteAllLines($manifest, $sourceFiles, [System.Text.UTF8Encoding]::new($false))
    & tar -czf .local/code-upload.tar.gz -T $manifest
    if ($LASTEXITCODE -ne 0) { throw 'Cannot package code' }
    & ssh -F ./ssh.config -o BatchMode=yes underwater-gpu 'mkdir -p /root/autodl-tmp/underwater-segmentation'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot connect to server' }
    & scp -F ./ssh.config -o BatchMode=yes .local/code-upload.tar.gz underwater-gpu:/root/autodl-tmp/underwater-segmentation/.code-upload.tar.gz
    if ($LASTEXITCODE -ne 0) { throw 'Upload failed' }
    & ssh -F ./ssh.config -o BatchMode=yes underwater-gpu 'cd /root/autodl-tmp/underwater-segmentation && tar -xzf .code-upload.tar.gz && echo CODE_SYNC_OK'
    if ($LASTEXITCODE -ne 0) { throw 'Remote extraction failed' }
} finally {
    Pop-Location
}
