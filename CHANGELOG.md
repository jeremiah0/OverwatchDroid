# Changelog

## v1.0.0 — 2026-10-12

First snapshot of the working Overwatch 2 setup on the AYN Thor.

- `ntdll.dll` pr47 for Proton Experimental (ARM64) `experimental-11.0-20261008`
  (sha256 `fb6022ab…392f`), plus Valve's original (`54140321…4046`) for rollback
- FEX `FEXCore-2610-d2rfix28` (libwow64fex / libarm64ecfex, .dll + .so)
- DroidDeck wiring: `desired.tsv` (Overwatch rows: pr47 ntdll, d2rfix28 FEX, dxvk 3.1.1,
  vkd3d-proton 3.0a) and `game-environment.json` (FEX TSO + vector TSO on, `FEX_SMCCHECKS=mtrack`)
- `patches/ntdll-pr47.bytediff` (161 bytes) to re-apply the patch to a new Proton build
- `install.sh`: checks root, DroidDeck and the exact Proton build, backs up, then merges only
  Overwatch's ntdll/fex rows and env entry. `--dry-run` and `--uninstall` (back to stock ntdll)
- Maintainer scripts: `pull.sh`, `verify.sh`, `release.sh`, `bytediff.py`
