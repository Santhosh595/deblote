#Requires -Version 5.1
# Deblote restore.ps1 — undo a Full clean. Run as Administrator.
# Restores services, hibernation, power plan, and unregisters schedules.
# Bloat apps come back from the Microsoft Store (links printed by Deblote log).
# Safest undo of all: System Restore → pick "Deblote clean" point.

$ErrorActionPreference = "Continue"
$id = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $id.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Run as Administrator: Right-click PowerShell → Run as Administrator." -ForegroundColor Red
    exit 1
}

Write-Host "=== Deblote restore ===" -ForegroundColor Cyan

powercfg /hibernate on
powercfg /setactive SCHEME_BALANCED
Write-Host "✓ Hibernation + Balanced plan restored."

foreach ($s in @("DiagTrack","dmwappushservice","MapsBroker","Fax","RemoteRegistry","RetailDemo","RemoteAccess","WPDBusEnum")) {
    Set-Service -Name $s -StartupType Automatic -ErrorAction SilentlyContinue
    Start-Service -Name $s -ErrorAction SilentlyContinue
}
Write-Host "✓ Services set back to Automatic."

foreach ($t in @("DebloteBootClean","DebloteBootCleanCleanup","DebloteMonthlyClean")) {
    Unregister-ScheduledTask -TaskName $t -Confirm:$false -ErrorAction SilentlyContinue
}
Write-Host "✓ Scheduled cleans removed."

Write-Host "`nBloat apps: re-install from Microsoft Store (YourPhone, Clipchamp, GetHelp, Candy Crush, Solitaire, etc.)."
Write-Host "Full undo: System Restore → restore point 'Deblote clean'."
