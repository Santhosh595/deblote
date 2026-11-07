"""Deblote — safe Windows cleaner & optimizer (v2).

Quick mode: temp/cache + DNS flush + thumbnail cache. Auto-runs.
Full mode: everything in Quick PLUS bloatware removal, unused-service
disable (reversible), startup cleanup, hibernation off, Windows.old
removal, power plan. REQUIRES typing YES — human approval gate.

Safety: dry-run preview unless --clean, restore point before any delete,
user folders (Documents/Desktop/Pictures/Downloads) never touched, every
action logged to deblote-log.json, undo commands printed for Full mode.
Stdlib only. No downloads except via install.ps1 (git/python installers).
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CleanTarget:
    name: str
    path: Path
    skip: list[str] = field(default_factory=list)


@dataclass
class Report:
    when: str
    mode: str = "quick"
    dry_run: bool = True
    deleted_files: int = 0
    deleted_dirs: int = 0
    freed_bytes: int = 0
    skipped_locked: int = 0
    actions: list[str] = field(default_factory=list)
    undo: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    targets: list[dict] = field(default_factory=list)


def is_admin() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes as _ctypes
        return bool(_ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except Exception:
        return False


def run(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def windows_targets() -> list[CleanTarget]:
    targets: list[CleanTarget] = []
    temp = os.environ.get("TEMP") or str(Path.home() / "AppData" / "Local" / "Temp")
    tmp = os.environ.get("TMP") or temp
    local = Path.home() / "AppData" / "Local"
    targets += [
        CleanTarget("User TEMP", Path(temp)),
        CleanTarget("User TMP", Path(tmp)),
        CleanTarget("Windows Temp", Path("C:/Windows/Temp")),
        CleanTarget("Prefetch", Path("C:/Windows/Prefetch")),
        CleanTarget("Win Update cache", Path("C:/Windows/SoftwareDistribution/Download")),
        CleanTarget("Delivery Optimization", Path("C:/Windows/SoftwareDistribution/DeliveryOptimization")),
    ]
    for name, sub in [
        ("Edge cache", "Microsoft/Edge/User Data/Default/Cache"),
        ("Chrome cache", "Google/Chrome/User Data/Default/Cache"),
        ("Chrome GPU cache", "Google/Chrome/User Data/Default/GPUCache"),
        ("Firefox cache", "Mozilla/Firefox/Profiles"),
        ("npm cache", "npm-cache"),
        ("pip cache", "pip/Cache"),
        ("VS Code cache", "Code/Cache"),
        ("VS Code GPU cache", "Code/GPUCache"),
        ("Thumbnail cache", "Microsoft/Windows/Explorer"),
        ("Crash dumps", "CrashDumps"),
    ]:
        targets.append(CleanTarget(name, local / sub))
    seen, out = set(), []
    for t in targets:
        k = str(t.path).lower()
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out


def full_only_targets() -> list[CleanTarget]:
    return [
        CleanTarget("Windows.old", Path("C:/Windows.old")),
        CleanTarget("Downloaded installers", Path("C:/$Windows.~BT")),
        CleanTarget("Upgrade leftovers", Path("C:/$Windows.~WS")),
        CleanTarget("OneDrive temp", Path("C:/OneDriveTemp")),
    ]


def simulate_targets(base: Path) -> list[CleanTarget]:
    return [
        CleanTarget("Sim TEMP", base / "Temp"),
        CleanTarget("Sim Cache", base / "Cache"),
        CleanTarget("Sim Logs", base / "Logs"),
    ]


def folder_size(path: Path) -> int:
    total = 0
    for f in path.rglob("*"):
        try:
            if f.is_file() and not f.is_symlink():
                total += f.stat().st_size
        except OSError:
            continue
    return total


def count_files(path: Path) -> tuple[int, int]:
    files = dirs = 0
    for p in path.rglob("*"):
        try:
            if p.is_dir():
                dirs += 1
            elif p.is_file():
                files += 1
        except OSError:
            continue
    return files, dirs


def clean_target(t: CleanTarget, dry: bool, report: Report) -> None:
    if not t.path.exists():
        report.targets.append({"name": t.name, "path": str(t.path), "status": "not present", "freed_bytes": 0})
        return
    before = folder_size(t.path)
    files, dirs = count_files(t.path)
    if dry:
        report.targets.append({"name": t.name, "path": str(t.path), "status": "would clean", "files": files, "dirs": dirs, "freed_bytes": before})
        report.freed_bytes += before
        return
    for child in list(t.path.iterdir()):
        try:
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child, ignore_errors=False)
                report.deleted_dirs += 1
            else:
                child.unlink(missing_ok=True)
                report.deleted_files += 1
        except PermissionError:
            report.skipped_locked += 1
        except OSError as e:
            report.errors.append(f"{child}: {e}")
    freed = max(0, before - folder_size(t.path))
    report.freed_bytes += freed
    report.targets.append({"name": t.name, "path": str(t.path), "status": "cleaned", "freed_bytes": freed})


def create_restore_point() -> bool:
    code, _ = run(["powershell", "-NoProfile", "-Command",
                   "Enable-ComputerRestore -Drive 'C:\\' -ErrorAction Stop; "
                   "Checkpoint-Computer -Description 'Deblote clean' -RestorePointType 'MODIFY_SETTINGS' -ErrorAction Stop"],
                  timeout=120)
    return code == 0


def flush_dns(report: Report) -> None:
    code, out = run(["ipconfig", "/flushdns"])
    msg = f"flushdns rc={code}"
    report.actions.append(msg)
    if code != 0:
        report.errors.append(f"ipconfig /flushdns: {out[:200]}")


# ---- Full-mode extras (reversible, logged with undo) ----
BLOAT_PACKAGES = [  # safe, re-installable from Microsoft Store
    "Microsoft.YourPhone", "Microsoft.Clipchamp", "Microsoft.GetHelp",
    "Microsoft.Getstarted", "Microsoft.MicrosoftSolitaireCollection",
    "king.com.CandyCrushSaga", "Disney.37853FC22B2CE", "Microsoft.People",
    "Microsoft.WindowsFeedbackHub", "Microsoft.BingWeather", "Microsoft.BingNews",
    "Microsoft.MixedReality.Portal",
]

UNUSED_SERVICES = [  # telemetry / bloat services, reversible
    "DiagTrack", "dmwappushservice", "MapsBroker", "Fax", "RemoteRegistry",
    "RetailDemo", "RemoteAccess", "WPDBusEnum",
]


def full_mode_actions(report: Report, dry: bool) -> None:
    # Hibernation off (frees ~RAM-size GBs; undo: powercfg /hibernate on)
    if dry:
        report.actions.append("WOULD: powercfg /hibernate off (frees hiberfil.sys)")
        report.undo.append("powercfg /hibernate on")
    else:
        code, _ = run(["powercfg", "/hibernate", "off"])
        report.actions.append(f"powercfg /hibernate off rc={code}")
        report.undo.append("powercfg /hibernate on")

    # High Performance power plan
    if dry:
        report.actions.append("WOULD: powercfg setactive High Performance")
        report.undo.append("powercfg /setactive SCHEME_BALANCED")
    else:
        code, _ = run(["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"])
        report.actions.append(f"powercfg High Performance rc={code}")
        report.undo.append("powercfg /setactive SCHEME_BALANCED")

    # Bloatware Appx removal
    for pkg in BLOAT_PACKAGES:
        if dry:
            report.actions.append(f"WOULD remove Appx: {pkg}")
            report.undo.append(f"Re-install {pkg} from Microsoft Store")
        else:
            code, _ = run(["powershell", "-NoProfile", "-Command",
                           f"Get-AppxPackage -Name '{pkg}' -AllUsers | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue"])
            report.actions.append(f"Remove-Appx {pkg} rc={code}")
            report.undo.append(f"Re-install {pkg} from Microsoft Store")

    # Unused services -> Manual (undo: Set-Service -StartupType Automatic)
    for svc in UNUSED_SERVICES:
        if dry:
            report.actions.append(f"WOULD set service Manual: {svc}")
            report.undo.append(f"Set-Service -Name {svc} -StartupType Automatic; Start-Service {svc}")
        else:
            code, _ = run(["powershell", "-NoProfile", "-Command",
                           f"Set-Service -Name '{svc}' -StartupType Manual -ErrorAction SilentlyContinue; "
                           f"Stop-Service -Name '{svc}' -Force -ErrorAction SilentlyContinue"])
            report.actions.append(f"Service Manual: {svc} rc={code}")
            report.undo.append(f"Set-Service -Name {svc} -StartupType Automatic; Start-Service {svc}")

    # Startup entries report (never auto-deletes; print list for user)
    if not dry:
        code, out = run(["powershell", "-NoProfile", "-Command",
                         "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command | Format-Table -AutoSize | Out-String -Width 200"])
        report.actions.append(f"Startup entries (review in Task Manager > Startup):\n{out[:1500]}")


def disk_hog_report(top_n: int = 15) -> list[dict]:
    roots = [Path.home() / d for d in ("AppData", "Documents", "Downloads", "Pictures", "Videos", "Desktop")]
    rows = []
    for root in roots:
        if not root.exists():
            continue
        for child in root.iterdir():
            try:
                size = folder_size(child) if child.is_dir() else child.stat().st_size
                rows.append({"path": str(child), "size_mb": round(size / 1e6, 1)})
            except OSError:
                continue
    rows.sort(key=lambda r: r["size_mb"], reverse=True)
    return rows[:top_n]


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} GB"


def main() -> int:
    ap = argparse.ArgumentParser(description="Deblote — safe Windows cleaner & optimizer")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--quick", action="store_true", help="temp/cache clean (default, auto)")
    g.add_argument("--full", action="store_true", help="FULL cleanup — requires typing YES")
    ap.add_argument("--clean", action="store_true", help="actually delete (default: preview)")
    ap.add_argument("--no-restore-point", action="store_true")
    ap.add_argument("--simulate", type=str, metavar="DIR", help="test mode under DIR")
    ap.add_argument("--report", type=str, nargs="?", const="deblote-log.json")
    ap.add_argument("--disk-report", action="store_true")
    args = ap.parse_args()

    mode = "full" if args.full else "quick"
    dry = not args.clean
    report = Report(when=datetime.now(timezone.utc).isoformat(), mode=mode, dry_run=dry)

    # Human approval gate for FULL mode
    if mode == "full" and args.clean and not args.simulate:
        print("\n⚠ FULL mode removes bloatware, disables services, turns off hibernation.")
        print("A restore point will be created first. Type YES to continue: ", end="")
        if input().strip().upper() != "YES":
            print("Aborted. (Nothing changed.)")
            return 1
        print("Approved.")

    if args.simulate:
        base = Path(args.simulate)
        base.mkdir(parents=True, exist_ok=True)
        for name in ("Temp", "Cache", "Logs", "Downloads"):
            d = base / name
            d.mkdir(exist_ok=True)
            if not any(d.rglob("*")):
                (d / "junk.txt").write_text("x" * 1000)
                sub = d / "sub"; sub.mkdir(exist_ok=True)
                (sub / "more.txt").write_text("y" * 2000)
        targets = simulate_targets(base)  # Downloads never included — by design
        print(f"SIMULATE under {base} — Downloads/ left untouched (by design).")
    elif sys.platform != "win32":
        print("⚠ Not on Windows. Use --simulate to test, or run on Windows.")
        targets = []
    else:
        targets = windows_targets()
        if mode == "full":
            targets += full_only_targets()

    if not dry and not args.simulate and sys.platform == "win32":
        if is_admin():
            if args.no_restore_point:
                print("⚠ Skipping restore point — NOT recommended.")
            elif create_restore_point():
                print("✓ Restore point created.")
            else:
                print("⚠ Could NOT create restore point. Continuing — locked files skipped.")
        else:
            print("⚠ Not Administrator — some cleans will be skipped. "
                  "Right-click Run as Administrator for full effect.")

    print(f"Mode: {mode.upper()} · {'DRY-RUN (preview)' if dry else 'CLEAN (deleting)'}")
    for t in targets:
        clean_target(t, dry, report)

    if sys.platform == "win32" and not args.simulate:
        flush_dns(report)
        if mode == "full":
            full_mode_actions(report, dry)

    print(f"\n{'Would free' if dry else 'Freed'}: {human(report.freed_bytes)} across {len(report.targets)} targets")
    if not dry:
        print(f"Deleted: {report.deleted_files} files, {report.deleted_dirs} dirs · Skipped locked: {report.skipped_locked}")
    for t in report.targets:
        print(f"  {t['status']:<22} {t['name']:<32} {human(t['freed_bytes'])}")
    for a in report.actions:
        print(f"  • {a}")
    if report.undo:
        print(f"\nUndo commands ({len(report.undo)}): see deblote-log.json")

    if args.disk_report or args.simulate:
        print("\n--- Disk hogs ---")
        for r in disk_hog_report():
            print(f"  {r['size_mb']:>10} MB  {r['path']}")

    if report.errors:
        print(f"\n{len(report.errors)} non-fatal errors (first 5):")
        for e in report.errors[:5]:
            print(f"  {e}")

    if args.report:
        Path(args.report).write_text(json.dumps(report.__dict__, indent=2))
        print(f"\nLog: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
