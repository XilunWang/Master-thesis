$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $publicKey = (Get-Content '.local/id_ed25519.pub' -Raw).Trim()
    if ($publicKey -notmatch '^ssh-ed25519 [A-Za-z0-9+/=]+(?: .*)?$') { throw 'Invalid public key' }
    # Pass the script over stdin to avoid Windows native-argument quote removal.
    # Only use the validated key fields; comments are not needed for login.
    $keyFields = $publicKey -split '\s+'
    $keyLine = $keyFields[0] + ' ' + $keyFields[1]
    $installScript = @'
set -eu
umask 077
mkdir -p ~/.ssh
touch ~/.ssh/authorized_keys
key='__PUBLIC_KEY__'
if ! grep -qxF -- "$key" ~/.ssh/authorized_keys; then
    printf '\n%s\n' "$key" >> ~/.ssh/authorized_keys
fi
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
echo PUBLIC_KEY_INSTALLED
'@
    $installScript = $installScript.Replace('__PUBLIC_KEY__', $keyLine).Replace("`r", '') + "`n"
    $encodedScript = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($installScript))
    $encodedScript | & ssh -F ./ssh.config -o PubkeyAuthentication=no -o PreferredAuthentications=password underwater-gpu 'base64 --decode --ignore-garbage | bash'
    if ($LASTEXITCODE -ne 0) { throw 'Public key installation failed' }
    & ssh -F ./ssh.config -o BatchMode=yes underwater-gpu 'echo SSH_KEY_OK; hostname; pwd'
    if ($LASTEXITCODE -ne 0) { throw 'Key login verification failed' }
    Write-Host 'Setup complete: SSH_KEY_OK means key login works.'
} finally {
    Pop-Location
}
