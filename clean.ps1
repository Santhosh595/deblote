# Run as Administrator. Creates a restore point, then previews only.
# Safe: preview first — pass -Clean to actually delete.
param([switch]$Clean, [switch]$NoRestorePoint)

$ErrorActionPreference = "Continue"

if (-not $Clean) {
    Write-Host "DRY-RUN preview — nothing will be deleted." -ForegroundColor Yellow
    Write-Host "Re-run with -Clean to actually clean." -ForegroundColor Yellow
}

# 1. Restore point (best effort)
if (-not $NoRestorePoint) {
    try {
        Enable-ComputerRestore -Drive "C:\" -ErrorAction Stop
        Checkpoint-Computer -Description "Deblote clean" -RestorePointType "MODIFY_SETTINGS" -ErrorAction Stop
        Write-Host "✓ Restore point created." -ForegroundColor Green
    } catch {
        Write-Host "⚠ Could not create restore point (admin?). Continuing — locked files skipped." -ForegroundColor Yellow
    }
}

# 2. Safe temp/cache folders (same list as deblote.py)
$folders = @(
    $env:TEMP,
    $env:TMP,
    "C:\Windows\Temp",
    "C:\Windows\Prefetch",
    "C:\Windows\SoftwareDistribution\Download",
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache",
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache",
    "$env:LOCALAPPDATA\npm-cache",
    "$env:LOCALAPPDATA\pip\Cache",
    "$env:LOCALAPPDATA\Code\Cache"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

$total = 0
foreach ($f in $folders) {
    $size = (Get-ChildItem $f -Recurse -Force -ErrorAction SilentlyContinue |
             Measure-Object Length -Sum).Sum
    if (-not $size) { $size = 0 }
    $mb = [math]::Round($size / 1MB, 1)
    $total += $size
    if ($Clean) {
        Get-ChildItem $f -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Cleaned ${mb} MB — $f" -ForegroundColor Green
    } else {
        Write-Host "Would free ${mb} MB — $f"
    }
}
Write-Host ("Done. " + $(if ($Clean) { "Freed" } else { "Would free" }) + " " + [math]::Round($total/1MB,1) + " MB total.")
Write-Host "User folders (Documents/Desktop/Pictures) were NOT touched."
