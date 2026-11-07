<div align="center">

# Deblote

### Clean Windows. Make old PCs fast again.

**One command. Zero bloat.**<br>
Temp & cache gone · Bloatware removed · Services tuned · Startup faster

[![Tests](https://github.com/Santhosh595/deblote/actions/workflows/test.yml/badge.svg)](https://github.com/Santhosh595/deblote/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4?logo=windows&logoColor=white)](https://github.com/Santhosh595/deblote)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PowerShell](https://img.shields.io/badge/PowerShell-7%2B-5391FE?logo=powershell&logoColor=white)](https://github.com/PowerShell/PowerShell)
[![Stars](https://img.shields.io/github/stars/Santhosh595/deblote?style=social)](https://github.com/Santhosh595/deblote/stargazers)
[![Forks](https://img.shields.io/github/forks/Santhosh595/deblote?style=social)](https://github.com/Santhosh595/deblote/forks)

</div>

---

## Quick Start — One Line

Open **PowerShell** (Win + X → Terminal) and paste:

```powershell
irm https://raw.githubusercontent.com/Santhosh595/deblote/main/install.ps1 | iex
```

**That's it.** Deblote will:

1. Check for **Git** → install via `winget` if missing
2. Check for **Python** → install if missing
3. Clone this repo → `C:\Users\<you>\deblote`
4. Run a **Quick preview** — nothing deleted until you say so

> **No hidden stuff.** `install.ps1` is ~70 lines. Read it in 2 minutes. The only URL it touches is GitHub.

---

## What It Looks Like

```powershell
PS C:\Users\you\deblote> python deblote.py --quick --clean

  Deblote — Quick clean (dry-run=False)
  ──────────────────────────────────
  [OK] Restore point created: "Deblote 2026-11-07 15:30"

  CLEAN  User TEMP .................... 1.2 GB
  CLEAN  Windows Temp ................. 340 MB
  CLEAN  Prefetch .....................  85 MB
  CLEAN  Windows Update cache ......... 2.1 GB
  CLEAN  Browser caches (Edge/Chrome) . 640 MB
  CLEAN  Dev caches (npm/pip/VS Code) . 910 MB
  DNS    flushed

  Freed: 5.27 GB  |  Skipped (locked): 3  |  Log: deblote-log.json
```

---

## Why Deblote?

| Feature | Deblote | CCleaner | Manual cleanup |
|---------|:-------:|:--------:|:--------------:|
| One-line install | Yes | No | No |
| Dry-run by default (preview first) | Yes | No | — |
| Restore point before deleting | Yes | Partial | No |
| Never touches Documents/Desktop/Downloads | Yes | Partial | — |
| Open source, no ads / "Pro" upsell | Yes (MIT) | No | — |
| Revoke bloat (Phone Link, Copilot…) | Full mode | No | No |
| Reboot-and-clean locked files | Auto | No | No |
| Monthly auto-clean (scheduled) | Yes | No | No |
| DISM + SFC repair built-in | Yes | No | No |
| One-click undo (`restore.ps1`) | Yes | No | No |
| Stdlib only — no `pip install` | Yes | — | — |

---

## Two Modes — Pick Your Level

### Quick — *Everyday cleanup (auto, safe)*
Perfect for weekly use. No bloat removal, no system changes.

```powershell
python deblote.py --quick --clean
```

### Full — *Deep clean (needs your approval)*
Removes bloat, tunes services, frees hibernation space, repairs Windows. **Asks you to type `YES` + requires Administrator.** Creates a Restore Point first. Logs every change so you can undo it.

```powershell
python deblote.py --full --clean
```

| Task | Quick | Full |
|------|:-----:|:----:|
| Temp / cache / update cache | Yes | Yes |
| DNS flush | Yes | Yes |
| Restore point first | Yes | Yes |
| `Windows.old` + upgrade leftovers (`$Windows.~BT`) | — | Yes |
| Bloatware apps removed (Phone Link, Clipchamp, Candy Crush, Solitaire…) | — | Yes |
| Bloat services → Manual (DiagTrack, Maps, Fax, RemoteRegistry…) | — | Yes, reversible |
| Hibernation off (frees GBs) | — | Yes |
| High Performance power plan | — | Yes |
| Startup list printed for you to trim | — | Yes |
| DISM `StartComponentCleanup` (WinSxS, GBs) | — | Yes |
| SFC `/scannow` (fixes corrupt system files) | — | Yes |
| Reboot-and-clean (locked files) | — | Scheduled |
| Monthly auto-clean | — | Scheduled |
| Disk health check (`chkdsk /scan` + free-space) | Report | Full check |
| Undo log → `deblote-log.json` + `restore.ps1` | — | Yes |

---

## What Gets Cleaned

**User TEMP/TMP** · **Windows Temp** · **Prefetch** · **Windows Update download cache** · **Edge/Chrome/Firefox caches** · **npm / pip / VS Code caches** · **Thumbnail cache** · **Crash dumps**

**Full mode adds:** `Windows.old` · `$Windows.~BT/WS` · hibernation file · bloatware apps & services · WinSxS via DISM · corrupt files via SFC

> **User folders are never touched** — Documents, Desktop, Pictures, Downloads, Videos — excluded by design, covered by a unit test.

---

## Locked Files? Handled.

Windows locks files that are in use. Deblote does three tiers:

1. **Read-only flag cleared** (`attrib -R`) — always, safe
2. **Full mode:** closes holder processes (Chrome, Edge, VS Code…), takes ownership (`icacls /takeown`)
3. **Still locked?** Registers **Reboot-and-clean** — runs automatically at next logon, then deletes itself. No more "access denied" frustration.

Anything still left is **honestly reported** as `locked left — reboot and re-run`, never faked as deleted.

---

## Undo Everything — `restore.ps1`

Changed your mind? One command puts it back:

```powershell
.\restore.ps1
```

- Hibernate back on · Balanced power plan
- Services → Automatic (DiagTrack, MapsBroker, Fax, RemoteRegistry, RetailDemo…)
- Unregisters reboot + monthly scheduled tasks
- **Plus:** System Restore Point is your ultimate undo — `rstrui.exe` → pick the Deblote point

---

## Security — Read This

- **No prompt-injection / invisible instructions.** Zero AI, zero LLM calls, zero data sent anywhere. Plain Python + PowerShell you can read in 10 minutes. Search the repo for `http` — the only URL is the GitHub clone in `install.ps1`.
- **Dry-run by default.** Running `deblote.py` with no flags deletes nothing.
- **Restore point before deleting.** Full mode additionally requires typing `YES` and Administrator rights.
- **User folders never touched.** Excluded by design + unit-tested.
- **Every action logged** to `deblote-log.json` with undo commands for Full mode.
- **Stdlib only.** No `pip install`, no admin needed for preview.

---

## What Deblote Does *NOT* Do (on purpose)

- No registry "cleaners" — that's how PCs get bricked.
- No fake "RAM booster" — close browser tabs, that actually works.
- No auto-uninstall of *your* programs — Full mode only removes pre-installed Windows bloat; everything else is listed and reversible.
- No telemetry, no ads, no "Pro" version. Ever.

---

## Requirements

| Need | Notes |
|------|-------|
| Windows 10 / 11 | 64-bit |
| PowerShell 5.1+ | Built-in, no install needed |
| Git + Python | **Auto-installed by `install.ps1`** if missing (via `winget`) |
| Administrator | Only for Full mode — the installer self-elevates if needed |

---

## Test It Anywhere (Linux / macOS too)

```bash
python deblote.py --simulate /tmp/deblote-test           # preview (no deletion)
python deblote.py --simulate /tmp/deblote-test --clean   # "clean" the fake tree
python -m unittest discover -s tests -v                  # 7 tests
```

All tests pass in CI on `windows-latest` — see the badge at the top.

---

## Files

| File | What |
|------|------|
| `install.ps1` | One-line bootstrapper — Git + Python check/install, clone, run |
| `deblote.py` | The cleaner — Quick + Full, DISM/SFC, schedulers, disk health |
| `clean.ps1` | PowerShell-only version (no Python needed) |
| `restore.ps1` | Undo a Full clean — restore services, power plan, hibernation, tasks |
| `tests/test_deblote.py` | Unit tests (incl. user-folder safety + locked-file honesty) |
| `.github/workflows/test.yml` | CI — runs tests on Windows on every push |

---

## Contributing

Issues & PRs welcome. Keep it simple: short functions, comments that explain *why*, stdlib only, dry-run by default. Run the tests before pushing:

```bash
python -m unittest discover -s tests -v
```

---

## Star History

<a href="https://star-history.com/#Santhosh595/deblote&Date">
  <img src="https://api.star-history.com/svg?repos=Santhosh595/deblote&type=Date" alt="Star History Chart">
</a>

---

## License

MIT — do whatever, no warranty. Windows is a trademark of Microsoft.

---

<div align="center">

**Keywords:** windows cleaner · windows debloat · pc optimizer · speed up windows · windows 11 debloater · system cleaner · temp cleaner · windows optimizer · bloatware remover · windows 10 speed up

If Deblote saved your old laptop, star the repo.

</div>
