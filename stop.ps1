$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
docker compose --profile playit down
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -match "dashboard\\app.py" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
$playit = "C:\Program Files\playit_gg\bin\playit.exe"
if (Test-Path $playit) {
    & $playit stop
}
