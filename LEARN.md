# Learn — deblote

## What it is

Windows cleaner/optimizer. Quick mode (temp/cache, auto) vs Full mode (bloatware, services, DISM/SFC, needs your `YES` + admin). One-line install, dry-run by default, restore point first, locked-file handling, reboot + monthly auto-clean, `restore.ps1` undo. Python stdlib + PowerShell, tested on Windows CI.

**Read this first, then go file-by-file in the repo.**

## 5-minute quickstart

```powershell
irm https://raw.githubusercontent.com/Santhosh595/deblote/main/install.ps1 | iex
# or locally, anywhere (Linux too, for tests):
git clone https://github.com/Santhosh595/deblote && cd deblote
python deblote.py --simulate /tmp/deblote-test            # preview only
python deblote.py --simulate /tmp/deblote-test --clean    # "clean" the fake tree
python -m unittest discover -s tests -v                  # 7 tests
```

## Concepts — the "why" behind each file

| If you see this in the code | What it means | Viva answer |
|---|---|---|
| `windows_targets()` (%TEMP%, Prefetch, etc.) | What "clean" means on Windows | Temp = safe; user folders = never touch (test-enforced) |
| Dry-run default (`--clean` required) | Preview before delete | Safety by default; you see the list before anything goes |
| Restore point (`vssadmin` / `Checkpoint-Computer`) | The safety net | Created *before* deleting; the ultimate undo |
| Bloat list (Phone Link, Clipchamp...) | Pre-installed UWP/AppX junk | `Get-AppxPackage` + `Remove-AppxPackage` |
| Services → Manual (DiagTrack...) | Telemetry/services perf win | Manual = starts on demand, not at boot |
| Hibernation off (`powercfg /hibernate off`) | Frees `hiberfil.sys` (GBs) | File is sized to RAM; tradeoff = no hibernate |
| DISM `StartComponentCleanup` | WinSxS cleanup | Windows component store, hardlinked files — GBs recoverable |
| SFC `/scannow` | System file repair | Verifies protected files against known-good copies |
| Locked-file tiers (`attrib -R`, kill holders, `icacls /takeown`) | Handling in-use files | Read-only → close holder process → take ownership → reboot-delete |
| Task Scheduler (`schtasks`) | Reboot-clean + monthly auto-clean | One-shot at logon vs recurring monthly |
| `restore.ps1` | Undo everything | Services back to Automatic, hibernate on, tasks removed |
| UTF-8 stdout fix (`reconfigure`) | Windows cp1252 can't print ✓/⚠ | Why CI failed and how it was fixed — a real war story |

## Common pitfalls

1. **Registry "cleaners"** — deblote deliberately does none. That's how PCs get bricked; say so.
2. **Touching user folders** — Documents/Desktop/Downloads are excluded and unit-tested. Never relax this.
3. **Deleting without a restore point** — order matters: point first, delete second.
4. **Faking success on locked files** — honestly report `locked left — reboot and re-run`.
5. **Full mode without `YES` gate** — the human approval is the feature. Don't automate it away.

## Hands-on, in this order

1. Run the simulate preview. What does it list? What does it skip and why?
2. Run `--simulate ... --clean` on a fake tree with a `Downloads` folder inside. Verify Downloads survives (the test does this too).
3. Read `windows_targets()`. Which target would you add next, and why?
4. Read the locked-file tiers. Which tier handles a file held by Chrome? By a service?
5. On real Windows: `python deblote.py --quick` (dry-run), read the list, then `--quick --clean`.
6. Ask: why does `StartComponentCleanup` reclaim GBs? (WinSxS hardlink dedup — learn this one cold.)

## Viva questions (with the trap)

1. **"DISM vs SFC?"** Answer: DISM repairs the component store and cleans WinSxS; SFC verifies protected system files. Different layers.
2. **"How do you delete a locked file?"** Answer: 3 tiers — clear readonly, close holder, take ownership; if still locked, reboot-delete. Trap: "just force delete".
3. **"Why a restore point *before*?"** Answer: after is useless; VSS snapshots at a point in time.
4. **"Why does hibernation off free space?"** Answer: `hiberfil.sys` ≈ RAM size; tradeoff is losing hibernate.
5. **"CI failed once — what happened?"** Answer: cp1252 stdout + `✓` print → `UnicodeEncodeError` on Windows runners only. Fixed by forcing UTF-8. This is a great war story.
6. **"Why Python stdlib only?"** Answer: no install, no supply-chain risk, runs anywhere.

## 3 things to say if stuck

- "Dry-run by default; nothing deletes without `--clean`."
- "User folders are excluded by design and by test."
- "Full mode has a human gate and a restore point — that's the safety model."

Good luck. This repo proves you can ship a real tool with real safety engineering.
