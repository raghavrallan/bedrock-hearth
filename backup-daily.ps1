param(
    [switch]$IfNeeded
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Container = "friends-smp"
$BackupRoot = "D:\Backup raghav\projects\friends-smp"
$KeepDays = 14
$Stamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$Today = Get-Date -Format "yyyy-MM-dd"
$MetaPath = Join-Path $BackupRoot "last-backup.json"
$LocalMetaPath = Join-Path $ProjectRoot "last-backup.json"
$LogPath = Join-Path $BackupRoot "backup.log"

$FallbackLog = Join-Path $ProjectRoot "backup-local.log"

function Write-Log([string]$Message) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    foreach ($target in @($LogPath, $FallbackLog)) {
        try {
            Add-Content -Path $target -Value $line -Encoding UTF8 -ErrorAction Stop
            return
        } catch {
            continue
        }
    }
}

. (Join-Path $ProjectRoot "notify.ps1")

$existing = $null
foreach ($source in @($MetaPath, $LocalMetaPath)) {
    try {
        if (Test-Path $source) {
            $existing = Get-Content $source -Raw -Encoding UTF8 | ConvertFrom-Json
            break
        }
    } catch {
        continue
    }
}

# Attempts reset each day, so a failure at 06:00 is attempt 1 and the 07:00 retry is attempt 2.
$Attempt = 1
if ($existing -and $existing.date -eq $Today -and $existing.attempts) {
    $Attempt = [int]$existing.attempts + 1
}

function Write-Meta([bool]$Ok, [string]$Detail, [string]$File, [double]$SizeMb) {
    $meta = [ordered]@{
        ok       = $Ok
        date     = $Today
        at       = (Get-Date -Format "yyyy-MM-dd HH:mm")
        detail   = $Detail
        attempts = $Attempt
        file     = $File
        sizeMb   = $SizeMb
    }
    foreach ($target in @($MetaPath, $LocalMetaPath)) {
        try {
            [System.IO.File]::WriteAllText($target, ($meta | ConvertTo-Json))
        } catch {
            continue
        }
    }
}

function Send-Mc([string]$Command) {
    & docker exec $Container send-command $Command | Out-Null
}

if (-not (Test-Path "D:\")) {
    $reason = "Drive D: is not available."
    Write-Log "Backup failed (attempt $Attempt): $reason"
    Write-Meta $false $reason "" 0
    Show-Toast "Friends SMP backup FAILED" "$reason Attempt $Attempt. Retrying in an hour."
    exit 1
}

New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

if ($IfNeeded -and $existing -and $existing.date -eq $Today -and $existing.ok -eq $true) {
    Write-Host "Backup already done today. Skipping."
    exit 0
}

$work = Join-Path $BackupRoot ("work-" + $Stamp)
$zip = Join-Path $BackupRoot ("friends-smp-" + $Stamp + ".zip")
$held = $false
$ok = $false

try {
    if ($Attempt -gt 1) {
        Write-Log ("Starting backup {0} (retry attempt {1} today)" -f $Stamp, $Attempt)
    } else {
        Write-Log "Starting backup $Stamp"
    }

    $inspect = & docker inspect $Container --format "{{.State.Running}}" 2>$null
    $exists = ($LASTEXITCODE -eq 0)
    $running = ($exists -and "$inspect".Trim() -eq "true")

    New-Item -ItemType Directory -Force -Path $work | Out-Null

    if ($running) {
        Send-Mc "save hold"
        $held = $true
        $ready = $false
        for ($i = 0; $i -lt 40; $i++) {
            Start-Sleep -Seconds 2
            Send-Mc "save query"
            $tail = (& docker logs --tail 30 $Container 2>&1 | Out-String)
            if ($tail -match "Data saved") {
                $ready = $true
                break
            }
        }
        if (-not $ready) {
            Write-Log "save query did not confirm; copying anyway"
        }
    }

    if ($exists) {
        & docker cp "${Container}:/data/worlds" (Join-Path $work "worlds")
        if ($LASTEXITCODE -ne 0) { throw "docker cp worlds failed" }
        $listing = & docker exec $Container ls /data
        foreach ($file in @("server.properties", "permissions.json", "allowlist.json", "whitelist.json")) {
            if ($listing -contains $file) {
                & docker cp "${Container}:/data/$file" (Join-Path $work $file)
            }
        }
    } else {
        $volume = "minecraft-server_mc-data"
        & docker run --rm -v "${volume}:/data:ro" -v "${work}:/out" busybox sh -c "cp -a /data/worlds /out/worlds; cp -f /data/server.properties /data/permissions.json /data/allowlist.json /data/whitelist.json /out/ 2>/dev/null; true"
        if ($LASTEXITCODE -ne 0) { throw "Volume copy failed. Is Docker running?" }
    }

    $envSrc = Join-Path $ProjectRoot ".env"
    if (Test-Path $envSrc) {
        Copy-Item $envSrc (Join-Path $work "server.env")
    }

    if ($held) {
        Send-Mc "save resume"
        $held = $false
    }

    if (Test-Path $zip) { Remove-Item $zip -Force }
    Compress-Archive -Path (Join-Path $work "*") -DestinationPath $zip -CompressionLevel Optimal
    Remove-Item $work -Recurse -Force

    $sizeMb = [math]::Round((Get-Item $zip).Length / 1MB, 1)
    Write-Meta $true "Backup completed." $zip $sizeMb

    Get-ChildItem -Path $BackupRoot -Filter "friends-smp-*.zip" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$KeepDays) } |
        ForEach-Object {
            Write-Log "Removing old backup $($_.Name)"
            Remove-Item $_.FullName -Force
        }

    $ok = $true
    $suffix = ""
    if ($Attempt -gt 1) { $suffix = " on attempt $Attempt today" }
    Write-Log "Backup done${suffix}: $zip ($sizeMb MB)"
    Show-Toast "Friends SMP backup OK" ("{0} MB saved at {1}{2}. Kept {3} days." -f $sizeMb, (Get-Date -Format 'HH:mm'), $suffix, $KeepDays)
} catch {
    $reason = $_.Exception.Message
    if (-not $reason) { $reason = "Unknown error." }
    Write-Log ("Backup failed (attempt {0}): {1}" -f $Attempt, $reason)
    Write-Meta $false $reason "" 0
    if ($held) {
        try { Send-Mc "save resume" } catch { }
    }
    if (Test-Path $work) {
        Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
    }
    Show-Toast "Friends SMP backup FAILED" ("Attempt {0}: {1} Retrying in an hour." -f $Attempt, $reason)
    exit 1
}

if (-not $ok) { exit 1 }
