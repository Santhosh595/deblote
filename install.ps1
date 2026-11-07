#Requires -Version 5.1
# Deblote one-line installer for Windows. Run this FIRST.
# It checks for Git + Python, installs them if missing (winget), clones the
# repo, then hands off to deblote.py. No downloads except Git/Python installers.
#
# Run from PowerShell:
#   irm https://raw.githubusercontent.com/Santhosh595/deblote/main/install.ps1 | iex
# Or locally:  .\install.ps1
#
# Security note: this script ONLY:
#   1. checks/installs Git + Python via winget (official Microsoft package manager)
#   2. clones THIS repo (Santhosh595/deblote) into %USERPROFILE%\deblote
#   3. runs deblote.py --quick (preview only, nothing deleted)
# No telemetry, no other URLs, no registry edits, no disabling of security.
# Read install.ps1 in the repo before running if you want to verify.

$ErrorActionPreference = "Continue"
$RepoUrl = "https://github.com/Santhosh595/deblote.git"
$Dest = Join-Path $env:USERPROFILE "deblote"

Write-Host "=== Deblote installer ===" -ForegroundColor Cyan

# 0. Self-elevate: most cleans need Administrator. Re-launch elevated once.
$id = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $id.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Not Administrator — re-launching elevated (click Yes on the prompt)..." -ForegroundColor Yellow
    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PSCommandPath)
    Start-Process powershell -Verb RunAs -ArgumentList $args
    # If launched via irm|iex (no file), fall back to manual instruction:
    if (-not $PSCommandPath) {
        Write-Host "Right-click PowerShell → Run as Administrator, then re-run the one-liner." -ForegroundColor Red
    }
    exit
}
Write-Host "✓ Running as Administrator"

# 1. Git
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "Git not found — installing via winget..." -ForegroundColor Yellow
    winget install --id Git.Git -e --source winget --silent `
        --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path","User")
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) { Write-Host "⚠ Git install failed. Install from https://git-scm.com and re-run." -ForegroundColor Red; exit 1 }
} else { Write-Host "✓ Git found: $($git.Source)" }

# 2. Python 3.11+
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "Python not found — installing via winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.12 -e --source winget --silent `
        --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path","User")
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { Write-Host "⚠ Python install failed. Install from https://python.org and re-run." -ForegroundColor Red; exit 1 }
} else { Write-Host "✓ Python found: $($py.Source)" }

# 3. Clone (or pull if already there)
if (Test-Path (Join-Path $Dest ".git")) {
    Write-Host "Repo exists — pulling latest..."
    git -C $Dest pull --ff-only
} else {
    Write-Host "Cloning $RepoUrl ..."
    git clone $RepoUrl $Dest
    if ($LASTEXITCODE -ne 0) { Write-Host "⚠ Clone failed (network?). Check connection and re-run." -ForegroundColor Red; exit 1 }
}

# 4. Run Quick preview (nothing deleted yet)
Write-Host "`n--- Deblote Quick preview (safe, nothing deleted) ---" -ForegroundColor Cyan
python (Join-Path $Dest "deblote.py") --quick

Write-Host "`nNext steps:" -ForegroundColor Green
Write-Host "  cd $Dest"
Write-Host "  python deblote.py --quick --clean        # actually clean temp/cache (fast, safe)"
Write-Host "  python deblote.py --full --clean         # FULL cleanup (asks YES first; removes bloatware, disables bloat services, hibernate off)"
Write-Host "  Logs: $Dest\deblote-log.json  (every action + undo commands)"
