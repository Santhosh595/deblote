<h1 align="center">🧹 Deblote</h1>

<p align="center"><b>Clean Windows. Make old PCs fast again.</b> Temp/cache rebuild, bloatware removed, bloat services off — in one command.</p>

<p align="center">
  <a href="https://github.com/Santhosh595/deblote/actions/workflows/test.yml"><img src="https://github.com/Santhosh595/deblote/actions/workflows/test.yml/badge.svg" alt="tests"></a>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
  <img src="https://img.shields.io/badge/platform-Windows-blue" alt="Windows">
  <img src="https://img.shields.io/badge/python-3.11%2B-yellow" alt="Python 3.11+">
</p>

## ⚡ One-line install (Windows PowerShell)

```powershell
irm https://raw.githubusercontent.com/Santhosh595/deblote/main/install.ps1 | iex
```

That checks for **Git** (installs via `winget` if missing) → checks for **Python** (installs if missing) → clones this repo → runs a **Quick preview**. Nothing is deleted until you say so.

> Prefer to read first? Open `install.ps1` — it's 60 lines and only does the 4 steps above. No telemetry, no other URLs.

## Two versions

| | ⚡ Quick (auto) | 🧹 Full (needs your `YES`) |
|---|---|---|
| Temp / cache / update cache | ✅ | ✅ |
| DNS flush | ✅ | ✅ |
| `Windows.old`, upgrade leftovers | — | ✅ |
| Bloatware apps removed (Phone Link, Clipchamp, Candy Crush, Solitaire…) | — | ✅ |
| Bloat services → Manual (DiagTrack, Maps, Fax, RetailDemo…) | — | ✅ (reversible) |
| Hibernation off (frees GBs) | — | ✅ |
| High Performance power plan | — | ✅ |
| Startup list printed | — | ✅ (you click in Task Manager) |
| Restore point first | ✅ | ✅ |
| Undo commands logged | — | ✅ (`deblote-log.json`) |

```powershell
cd $env:USERPROFILE\deblote
python deblote.py --quick --clean     # fast + safe
python deblote.py --full --clean      # FULL — asks YES first
```

## That's it — what gets cleaned

User TEMP/TMP · Windows Temp · Prefetch · Windows Update download cache ·
Edge/Chrome/Firefox caches · npm/pip/VS Code caches · thumbnail cache ·
crash dumps. In Full mode also: `Windows.old`, `$Windows.~BT/WS`, hibernation file.

## 🔒 Security — read this

- **No prompt-injection / invisible instructions.** This repo contains zero AI, zero LLM calls, zero data sent anywhere. Every file is plain Python + PowerShell you can read in 10 minutes. Search the repo for `http` — the only URL is the GitHub clone in `install.ps1`.
- **Dry-run by default.** Running `deblote.py` with no flags deletes nothing.
- **Restore point before deleting.** Full mode additionally requires typing `YES` and Administrator rights.
- **User folders are never touched.** Documents, Desktop, Pictures, Downloads, Videos are excluded by design (and covered by a unit test).
- **Every action is logged** to `deblote-log.json` with undo commands for Full mode.
- **Stdlib only.** No `pip install`, no admin needed for preview.

## What Deblote does NOT do (on purpose)

- No registry "cleaners" — that's how PCs get bricked.
- No fake "RAM booster" — close browser tabs, that actually works.
- No auto-uninstall of your programs — Full mode only removes pre-installed Windows bloat; everything else is listed and reversible.

## Test it anywhere (Linux/macOS too)

```bash
python deblote.py --simulate /tmp/deblote-test           # preview
python deblote.py --simulate /tmp/deblote-test --clean   # "clean" the fake tree
python -m unittest discover -s tests -v                 # 5 tests
```

## Files

| File | What |
|---|---|
| `install.ps1` | One-line bootstrapper (Git + Python check/install, clone, run) |
| `deblote.py` | The cleaner (Quick + Full) — run this |
| `clean.ps1` | PowerShell-only version (no Python needed) |
| `tests/test_deblote.py` | Unit tests |

## License

MIT — do whatever, no warranty. Windows is a trademark of Microsoft.
