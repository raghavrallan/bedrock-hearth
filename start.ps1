$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$playit = "C:\Program Files\playit_gg\bin\playit.exe"

Write-Host "Starting Minecraft Bedrock..."
docker compose up -d bedrock
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose failed. Is Docker Desktop running?"
}

if (Test-Path $playit) {
    $status = & $playit status 2>&1 | Out-String
    if ($status -notmatch "Phase: running|connected|online") {
        & $playit start | Out-Null
    }
}

Write-Host "Waiting for the world to load..."
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    $logs = docker logs friends-smp 2>&1 | Out-String
    if ($logs -match "Server started") {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}

if ($ready) {
    Write-Host "Friends SMP is online."
} else {
    Write-Host "Still starting. Check: docker compose logs -f bedrock"
}

$listening = Get-NetTCPConnection -LocalPort 8088 -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
    Start-Process -FilePath "python" -ArgumentList "`"$PSScriptRoot\dashboard\app.py`"" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
    Start-Sleep -Seconds 1
}
Start-Process -FilePath "powershell" -WindowStyle Hidden -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\backup-run.ps1`" -IfNeeded"

Write-Host ""
Write-Host "Same Wi-Fi:  192.168.1.4   port 19132"
Write-Host "Dashboard:   http://127.0.0.1:8088"
if (Test-Path $playit) {
    Write-Host "Internet:    run playit attach, or check https://playit.gg/account/tunnels"
}
