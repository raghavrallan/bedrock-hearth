# Rebuilds the X-ray resource pack from addons/xray-blocks.txt.
# Edit that list to hide more (or fewer) blocks, then re-run this.
# Entries are paths relative to textures/blocks/, without .png
# (e.g. "dirt" or "deepslate/deepslate"). Names must match vanilla
# Bedrock texture paths from Mojang/bedrock-samples.

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$PackRoot = Join-Path $PSScriptRoot "xray"
$BlockList = Join-Path $PSScriptRoot "xray-blocks.txt"
$TexDir = Join-Path $PackRoot "textures\blocks"
$Dist = Join-Path $ProjectRoot "dist"
$McPack = Join-Path $Dist "friends-smp-xray.mcpack"

if (-not (Test-Path $BlockList)) { throw "Missing block list: $BlockList" }
if (-not (Test-Path (Join-Path $PackRoot "manifest.json"))) { throw "Missing manifest in $PackRoot" }

$blocks = Get-Content $BlockList | ForEach-Object { $_.Trim() } | Where-Object { $_ -and $_ -notmatch '^\s*#' }
# Allow either "dirt" or legacy "dirt.png" in the list.
$blocks = $blocks | ForEach-Object { $_ -replace '\.png$','' }
$ores = $blocks | Where-Object { $_ -match "_ore|ancient_debris|gilded" }
if ($ores) { throw "Block list contains ore textures, which would hide them: $($ores -join ', ')" }

if (Test-Path $TexDir) { Remove-Item $TexDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $TexDir | Out-Null

$bmp = New-Object System.Drawing.Bitmap 16, 16, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::FromArgb(0, 0, 0, 0))
$g.Dispose()
foreach ($name in $blocks) {
    $rel = $name.Replace('/', [IO.Path]::DirectorySeparatorChar) + ".png"
    $path = Join-Path $TexDir $rel
    $parent = Split-Path $path -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
}
$bmp.Dispose()
Write-Host "Generated $($blocks.Count) transparent textures."

New-Item -ItemType Directory -Force -Path $Dist | Out-Null
if (Test-Path $McPack) { Remove-Item $McPack -Force }

# Compress-Archive writes '\' in zip entry paths, which Bedrock cannot read.
$fs = [System.IO.File]::Open($McPack, [System.IO.FileMode]::Create)
$zip = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
foreach ($file in Get-ChildItem $PackRoot -Recurse -File) {
    $rel = $file.FullName.Substring($PackRoot.Length + 1).Replace('\', '/')
    $entry = $zip.CreateEntry($rel, [System.IO.Compression.CompressionLevel]::Optimal)
    $stream = $entry.Open()
    $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Dispose()
}
$zip.Dispose()
$fs.Dispose()

Write-Host ("Built {0} ({1} KB)" -f $McPack, [math]::Round((Get-Item $McPack).Length / 1KB, 1))
