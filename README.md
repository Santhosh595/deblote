# Deblote 🧹

**Clean Windows temp/cache to make old PCs feel faster.** Old PCs pile up temp files, update caches, browser caches, and build caches — none of that is your data, and Windows/apps just rebuild it. Deblote removes exactly that, safely.

## Safety first
- **Dry-run by default** — `python deblote.py` only previews. Add `--clean` to delete.
- **Restore point first** — asks Windows to snapshot before any delete (run as Administrator).
- **Never touches user folders** — Documents, Desktop, Pictures, Videos, Downloads are excluded by design.
- **Skips locked files** — anything in use is left alone, counted in the report.
- **Stdlib only** — no `pip install`, no admin needed for preview.

## What it cleans
User TEMP/TMP · Windows Temp · Prefetch · Windows Update download cache ·
Edge/Chrome/Firefox caches · npm/pip cache · VS Code cache · thumbnail cache.
Full list in `windows_targets()` in `deblote.py`.

## Usage (Windows)
```powershell
# 1. Preview (nothing deleted)
python deblote.py

# 2. Clean (creates restore point first; run PowerShell as Administrator)
python deblote.py --clean

# 3. Just the disk-hog report (what's eating space)
python deblote.py --disk-report

# PowerShell-only version (preview -> -Clean to delete)
.\clean.ps1
.\clean.ps1 -Clean
```

## Test from Linux/macOS
```bash
python deblote.py --simulate /tmp/deblote-test      # preview
python deblote.py --simulate /tmp/deblote-test --clean  # actually "clean" the fake tree
```
Simulation builds a fake Temp/Cache/Logs/Downloads tree and proves Downloads
is left untouched.

## Files
| File | What |
|---|---|
| `deblote.py` | The cleaner (Python stdlib only) — run this |
| `clean.ps1` | PowerShell-only equivalent |
| `tests/test_deblote.py` | 6 tests — run `python -m unittest discover -s tests -v` |
| `README.md` | This file |

## What Deblote does NOT do (by design)
- No registry "cleaners" — registry edits are how PCs get bricked.
- No startup manager / uninstaller — use Task Manager → Startup, Settings → Apps.
- No "RAM booster" snake oil — close browser tabs, that's real.
