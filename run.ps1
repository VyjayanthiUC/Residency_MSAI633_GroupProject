# Start the landing page + chat on http://127.0.0.1:8800 (chat at /chat) (Windows PowerShell equivalent of run.sh).
# Settings come from .env at the repo root (see .env.example).
# Usage:  powershell -ExecutionPolicy Bypass -File .\run.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (Test-Path .env) {
    foreach ($line in Get-Content .env) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim().Trim('"'), 'Process')
        }
    }
}
if (-not $env:LLM_API_KEY -and -not $env:ZAI_API_KEY) {
    Write-Error 'LLM_API_KEY is not set. Copy .env.example to .env and fill it in.'
}

# Chainlit's history sidebar needs auth, and auth needs a token-signing secret: generated once, kept in artifacts\
$secretFile = 'artifacts\.chainlit_auth_secret'
if (-not $env:CHAINLIT_AUTH_SECRET) {
    New-Item -ItemType Directory -Force artifacts | Out-Null
    if (-not (Test-Path $secretFile) -or (Get-Item $secretFile).Length -eq 0) {
        $bytes = New-Object byte[] 48
        [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
        [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_') | Set-Content -NoNewline -Encoding ascii $secretFile
    }
    $env:CHAINLIT_AUTH_SECRET = (Get-Content $secretFile -Raw).Trim()
}
$port = if ($env:PORT) { $env:PORT } else { '8800' }

# One server (web\server.py): the landing page at / with the chat widget, and the full Chainlit chat at /chat
uv run uvicorn web.server:app --host 127.0.0.1 --port $port @args
