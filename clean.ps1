#Requires -Version 5.1
# Deblote — PowerShell-only cleaner (no Python needed).
# Default: PREVIEW only. Pass -Clean to delete. Pass -Full for bloatware/services
# (Full asks "YES" first and creates a restore point — human approval required).
param([switch]$Clean, [switch]$Full)

$ErrorActionPreference = "Continue"

function Assert-Admin {
    $id = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
    return $id.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not $Clean) {
    Write-Host "DRY-RUN preview — nothing deleted. Add -Clean to actually clean." -ForegroundColor Yellow
}
if ($Full) {
    Write-Host "`n⚠ FULL mode: bloatware removal, disables bloat services, hibernate off, High Performance plan." -ForegroundColor Red
    Write-Host "Run as Administrator — a restore point will be created first." -ForegroundColor Yellow
    if ($Clean) {
        if (-not (Assert-Admin)) { Write-Host "✗ Full mode needs Administrator. Right-click PowerShell → Run as Administrator." -ForegroundColor Red; exit 1 }
        $a = Read-Host "Type YES to continue"
        if ($a -ne "YES") { Write-Host "Aborted."; exit 1 }
        try {
            Enable-ComputerRestore -Drive "C:\" -ErrorAction Stop
            Checkpoint-Computer -Description "Deblote full clean" -RestorePointType "MODIFY_SETTINGS" -ErrorAction Stop
            Write-Host "✓ Restore point created." -ForegroundColor Green
        } catch { Write-Host "⚠ Restore point failed — continuing (locked files skipped)." -ForegroundColor Yellow }
    }
}

$folders = @($env:TEMP, $env:TMP, "C:\Windows\Temp", "C:\Windows\Prefetch",
    "C:\Windows\SoftwareDistribution\Download",
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache",
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache",
    "$env:LOCALAPPDATA\npm-cache", "$env:LOCALAPPDATA\pip\Cache",
    "$env:LOCALAPPDATA\Code\Cache") | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

$total = 0
foreach ($f in $folders) {
    $size = (Get-ChildItem $f -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    if (-not $size) { $size = 0 }
    $mb = [math]::Round($size / 1MB, 1); $total += $size
    if ($Clean) {
        Get-ChildItem $f -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Cleaned ${mb} MB — $f" -ForegroundColor Green
    } else { Write-Host "Would free ${mb} MB — $f" }
}

if ($Full) {
    if ($Clean) {
        powercfg /hibernate off
        powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
        $pkgs = @("Microsoft.YourPhone","Microsoft.Clipchamp","Microsoft.GetHelp","Microsoft.Getstarted",
                  "Microsoft.MicrosoftSolitaireCollection","king.com.CandyCrushSaga","Microsoft.WindowsFeedbackHub")
        foreach ($p in $pkgs) { Get-AppxPackage -Name $p -AllUsers -ErrorAction SilentlyContinue | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue }
        foreach ($s in @("DiagTrack","dmwappushservice","MapsBroker","Fax","RetailDemo")) {
            Set-Service -Name $s -StartupType Manual -ErrorAction SilentlyContinue
            Stop-Service -Name $s -Force -ErrorAction SilentlyContinue }
        Write-Host "✓ Full actions done. Undo: powercfg /hibernate on; Set-Service -StartupType Automatic." -ForegroundColor Green
    } else { Write-Host "Would: hibernate off, High Performance plan, remove 7 bloat apps, set 5 services Manual." }
}

Write-Host ("Done. " + $(if ($Clean) { "Freed" } else { "Would free" }) + " " + [math]::Round($total/1MB,1) + " MB.")
Write-Host "User folders (Documents/Desktop/Pictures/Downloads) were NOT touched."
