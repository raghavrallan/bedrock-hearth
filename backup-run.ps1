$ProjectRoot = $PSScriptRoot
$BackupRoot = "D:\Backup raghav\projects\friends-smp"
$Script = Join-Path $ProjectRoot "backup-daily.ps1"
$MetaPaths = @((Join-Path $BackupRoot "last-backup.json"), (Join-Path $ProjectRoot "last-backup.json"))
$LogPaths = @((Join-Path $BackupRoot "backup.log"), (Join-Path $ProjectRoot "backup-local.log"))

. (Join-Path $ProjectRoot "notify.ps1")

function Write-Failure([string]$Reason) {
    $line = "{0}  Backup runner failed: {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Reason
    Write-Host $line
    foreach ($log in $LogPaths) {
        try {
            Add-Content -Path $log -Value $line -Encoding UTF8 -ErrorAction Stop
            break
        } catch {
            continue
        }
    }
    $today = Get-Date -Format "yyyy-MM-dd"
    $attempt = 1
    foreach ($path in $MetaPaths) {
        try {
            if (Test-Path $path) {
                $prev = Get-Content $path -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($prev.date -eq $today -and $prev.attempts) { $attempt = [int]$prev.attempts + 1 }
                break
            }
        } catch {
            continue
        }
    }
    $meta = [ordered]@{
        ok       = $false
        date     = $today
        at       = (Get-Date -Format "yyyy-MM-dd HH:mm")
        detail   = $Reason
        attempts = $attempt
        file     = ""
        sizeMb   = 0
    }
    foreach ($path in $MetaPaths) {
        try {
            [System.IO.File]::WriteAllText($path, ($meta | ConvertTo-Json))
        } catch {
            continue
        }
    }
    Show-Toast "Friends SMP backup FAILED" $Reason
}

if (-not (Test-Path $Script)) {
    Write-Failure "backup-daily.ps1 is missing from $ProjectRoot."
    exit 1
}

# A parse error stops the whole file from running, so it can never report itself.
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($Script, [ref]$null, [ref]$parseErrors)
if ($parseErrors -and $parseErrors.Count -gt 0) {
    $first = $parseErrors[0]
    Write-Failure ("backup-daily.ps1 has a syntax error on line {0}: {1}" -f $first.Extent.StartLineNumber, $first.Message)
    exit 1
}

$startedAt = Get-Date
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Script @args
$code = $LASTEXITCODE

if ($code -ne 0) {
    $reported = $false
    foreach ($path in $MetaPaths) {
        if ((Test-Path $path) -and (Get-Item $path).LastWriteTime -ge $startedAt) {
            $reported = $true
            break
        }
    }
    if (-not $reported) {
        Write-Failure "backup-daily.ps1 exited with code $code without reporting a reason."
    }
}

exit $code
