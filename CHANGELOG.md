# Changelog

## v1.2.0 — 2026-10-12

- Lower graphics settings: every quality option at its lowest, 50% render scale with AMD FSR 1.0,
  and a 30 fps cap. The values are the ones Overwatch saves itself.
- README rewritten to be shorter. Added tips for giving Overwatch the fastest CPU core and using
  Snapdragon GSR in DroidDeck, and corrected the note on saving settings (Overwatch saves when you
  quit from its menu).

## v1.1.0 — 2026-10-12

- Installer sets Overwatch's `Settings_v0.ini` to the **Low preset + DirectX 12** (other settings kept).
  Overwatch was getting killed before it could save its own settings, so in-game changes never stuck.
- Installer writes the pr47 `ntdll.dll` directly into Proton Experimental (ARM64) as well. DroidDeck can
  drop hand-added `ntdll` rows from `desired.tsv` and delete their store folders, but it leaves Proton's file alone.
  `--uninstall` puts the stock file back the same way.
- `verify.sh` reports what's actually in effect: Proton's `ntdll.dll`, store folders (missing is OK), Overwatch rows.
- README: stability section. Mid-match closes are Android's low-memory killer, not a game crash.
- Repo cleanup: the reference device's backups, full `desired.tsv` and logs are no longer published;
  `config/game-environment.json` only has Overwatch's entry.

## v1.0.1 — 2026-10-12

- Installer finds DroidDeck by its files instead of assuming the antutu package
  (`com.antutu.benchmark.full`), so the standard (`com.droiddeck.launcher`), ludashi and pubg
  variants work too. With several variants installed it prefers the one that has the required
  Proton build, or asks you to pick with `DROIDDECK_PACKAGE`.
- Clearer errors when root is missing or DroidDeck isn't found.

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
