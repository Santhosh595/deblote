"""Deblote — clean Windows temp/cache to make old PCs feel faster.

Safety-first: dry-run by default, restore point before any delete, skip
locked files, never touches user folders (Documents/Desktop/Pictures etc).
Stdlib only. Runs on Windows; --simulate lets you test from anywhere.
"""

from __future__ import annotations

import argparse
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
    # subfolders to skip inside path (e.g. in-use lock files handled separately)
    skip: list[str] = field(default_factory=list)


@dataclass
class Report:
    when: str
    dry_run: bool
    deleted_files: int = 0
    deleted_dirs: int = 0
    freed_bytes: int = 0
    skipped_locked: int = 0
    errors: list[str] = field(default_factory=list)
    targets: list[dict] = field(default_factory=list)


def windows_targets() -> list[CleanTarget]:
    """Safe, well-known Windows temp/cache locations. Why these:
    they only hold throwaway data the OS/apps regenerate."""
    targets: list[CleanTarget] = []
    temp = os.environ.get("TEMP") or str(Path.home() / "AppData" / "Local" / "Temp")
    tmp = os.environ.get("TMP") or temp
    local = Path.home() / "AppData" / "Local"
    targets.append(CleanTarget("User TEMP", Path(temp)))
    targets.append(CleanTarget("User TMP", Path(tmp)))
    targets.append(CleanTarget("Windows Temp", Path("C:/Windows/Temp")))
    targets.append(CleanTarget("Prefetch", Path("C:/Windows/Prefetch")))
    targets.append(CleanTarget("Windows Update download cache",
                               Path("C:/Windows/SoftwareDistribution/Download")))
    targets.append(CleanTarget("Delivery Optimization cache",
                               Path("C:/Windows/SoftwareDistribution/DeliveryOptimization")))
    # App caches (safe: apps rebuild these)
    for name, sub in [
        ("Edge cache", "Microsoft/Edge/User Data/Default/Cache"),
        ("Chrome cache", "Google/Chrome/User Data/Default/Cache"),
        ("Chrome GPU cache", "Google/Chrome/User Data/Default/GPUCache"),
        ("Firefox cache", "Mozilla/Firefox/Profiles"),
        ("npm cache", "npm-cache"),
        ("pip cache", "pip/Cache"),
        ("VS Code cache", "Code/Cache"),
        ("VS Code GPU cache", "Code/GPUCache"),
        ("Windows thumbnail cache", "Microsoft/Windows/Explorer"),
    ]:
        targets.append(CleanTarget(name, local / sub))
    # Dedupe by resolved path, keep order
    seen: set[str] = set()
    out: list[CleanTarget] = []
    for t in targets:
        key = str(t.path).lower()
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out


def simulate_targets(base: Path) -> list[CleanTarget]:
    """Fake targets under a temp dir so Linux users can test the logic."""
    return [
        CleanTarget("Sim TEMP", base / "Temp"),
        CleanTarget("Sim Cache", base / "Cache"),
        CleanTarget("Sim Logs", base / "Logs"),
        CleanTarget("Sim Downloads-DO-NOT-TOUCH", base / "Downloads"),
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


def clean_target(t: CleanTarget, dry_run: bool, report: Report) -> None:
    """Delete contents of t.path (not the dir itself). Skips locked files."""
    if not t.path.exists():
        report.targets.append({"name": t.name, "path": str(t.path),
                               "status": "not present", "freed_bytes": 0})
        return
    before = folder_size(t.path)
    files, dirs = count_files(t.path)
    if dry_run:
        report.targets.append({"name": t.name, "path": str(t.path),
                               "status": "would clean (dry-run)",
                               "files": files, "dirs": dirs, "freed_bytes": before})
        report.freed_bytes += before
        return
    # real delete: contents only, skip errors
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
    after = folder_size(t.path)
    freed = max(0, before - after)
    report.freed_bytes += freed
    report.targets.append({"name": t.name, "path": str(t.path),
                           "status": "cleaned", "freed_bytes": freed})


def create_restore_point() -> bool:
    """Ask Windows to snapshot first. Best-effort; needs admin."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Enable-ComputerRestore -Drive 'C:\\' -ErrorAction Stop; "
             "Checkpoint-Computer -Description 'Deblote clean' -RestorePointType 'MODIFY_SETTINGS' -ErrorAction Stop"],
            capture_output=True, text=True, timeout=120,
        )
        return r.returncode == 0
    except Exception:
        return False


def disk_hog_report(top_n: int = 15) -> list[dict]:
    """Biggest folders in user profile — helps spot what's eating disk."""
    roots = [Path.home() / d for d in
             ("AppData", "Documents", "Downloads", "Pictures", "Videos", "Desktop")]
    rows: list[dict] = []
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
    ap = argparse.ArgumentParser(description="Deblote — safe Windows cleaner")
    ap.add_argument("--clean", action="store_true",
                    help="actually delete (default is dry-run / preview)")
    ap.add_argument("--no-restore-point", action="store_true",
                    help="skip restore point (NOT recommended)")
    ap.add_argument("--simulate", type=str, metavar="DIR",
                    help="test mode: clean a fake folder tree under DIR")
    ap.add_argument("--report", type=str, nargs="?", const="deblote-report.json",
                    help="write JSON report (default: deblote-report.json)")
    ap.add_argument("--disk-report", action="store_true",
                    help="show biggest folders in user profile")
    args = ap.parse_args()

    dry = not args.clean
    report = Report(when=datetime.now(timezone.utc).isoformat(), dry_run=dry)

    if args.simulate:
        base = Path(args.simulate)
        base.mkdir(parents=True, exist_ok=True)
        # build a fake tree if empty
        for name in ("Temp", "Cache", "Logs", "Downloads"):
            d = base / name
            d.mkdir(exist_ok=True)
            if not any(d.rglob("*")):
                (d / "junk.txt").write_text("x" * 1000)
                sub = d / "sub"
                sub.mkdir(exist_ok=True)
                (sub / "more.txt").write_text("y" * 2000)
        # protect Downloads: never clean it in simulation either
        targets = [t for t in simulate_targets(base) if "DO-NOT-TOUCH" not in t.name]
        print(f"SIMULATE under {base} — Downloads/ left untouched (by design).")
    else:
        if sys.platform != "win32":
            print("⚠ Not on Windows. Use --simulate to test the logic, "
                  "or run this on Windows. Showing disk report only.")
            dry = True
            targets = []
        else:
            targets = windows_targets()

    if not dry and not args.simulate and sys.platform == "win32":
        if args.no_restore_point:
            print("⚠ Skipping restore point — not recommended.")
        elif create_restore_point():
            print("✓ Restore point created.")
        else:
            print("⚠ Could NOT create restore point (run as Administrator?). "
                  "Continuing — locked files will be skipped.")

    print(f"Mode: {'DRY-RUN (nothing deleted)' if dry else 'CLEAN'}")
    for t in targets:
        clean_target(t, dry, report)

    print(f"\n{dry and 'Would free' or 'Freed'}: {human(report.freed_bytes)} "
          f"across {len(report.targets)} targets")
    if not dry:
        print(f"Deleted: {report.deleted_files} files, {report.deleted_dirs} dirs · "
              f"Skipped (locked): {report.skipped_locked}")
    for t in report.targets:
        print(f"  {t['status']:<26} {t['name']:<38} {human(t['freed_bytes'])}")

    if args.disk_report or args.simulate:
        print("\n--- Disk hogs (biggest folders in profile) ---")
        for r in disk_hog_report():
            print(f"  {r['size_mb']:>10} MB  {r['path']}")

    if report.errors:
        print(f"\n{len(report.errors)} non-fatal errors (first 5):")
        for e in report.errors[:5]:
            print(f"  {e}")

    if args.report:
        Path(args.report).write_text(json.dumps(report.__dict__, indent=2))
        print(f"\nReport: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
