# Changelog

## Unreleased

- README: link to a video of it running on the Thor.
- Frame rate cap raised from 30 to 90 fps. The README explains it's a ceiling; expect 30 to 60 in matches.
- README: fuller account-risk note (Steam Deck status, anti-cheat under Proton, the 2018 Linux bans Blizzard reversed).
- README: "Read this first" section on the unreviewed ntdll patch, Blizzard account risk and single-device
  testing, and a Credits section with thanks and the licenses of the bundled files.
- README and installer no longer say other games are unaffected: the patched `ntdll.dll` is shared by every
  game on Proton Experimental (ARM64). The README links the patch's source, GameNative/proton-wine#47.

## v1.4.0 — 2026-10-12

- One-step install: `bash install.sh` from the top folder checks everything, shows what will change and asks
  before touching the device. `--dry-run`, `--uninstall` and the new `--yes` still work; `--help` lists them.
- The installer offers to close DroidDeck instead of stopping, and lets you pick when several devices or
  DroidDeck installs are found.
- Plain fixes in error messages: missing adb or python3, USB debugging not allowed, no root, wrong Proton build.
- `--uninstall` works when DroidDeck has dropped the Overwatch `ntdll` rows, and says when there's nothing to undo.
- Faster settings, built on the tested Thor's current ones: High Quality Upsampling off (Default, no FSR),
  Reduce Buffering off, intro video skipped.
- README reorganised for new users: requirements with install commands, a three-step install, recommended
  settings, and a troubleshooting table.

## v1.3.0 — 2026-10-12

- FEX vector TSO off for Overwatch (`FEX_VECTORTSOENABLED=0`) to save CPU. Main TSO stays on.
- Installer also writes DroidDeck's master `game-environment.json` in the app folder. Before, it only wrote the
  copy in the Linux root, which DroidDeck overwrites at every session start, so FEX settings didn't stick.
- High Quality Upsampling set to `1` (meant to be AMD FSR 1.0; the README says to check the in-game label).
- `verify.sh` no longer stops when DroidDeck has deleted the store folders, and shows Overwatch's TSO settings.
- README: FEX settings table.

## v1.2.1 — 2026-10-12

- Installer no longer sets High Quality Upsampling. The value it set was FSR 2.2; the README now says to
  pick AMD FSR 1.0 in game.
- README: DroidDeck settings table from the tested Thor (all cores to the game, GPU clock held, realtime
  gamescope queue, ntsync, Snapdragon GSR, Win-FG 2×) and tips on heat and the Steam overlay.

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
