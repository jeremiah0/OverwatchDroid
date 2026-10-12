# Overwatch Droid

Overwatch 2 (Steam app `2357570`) on the AYN Thor through DroidDeck + Proton Experimental (ARM64) + FEX.

This repo is a snapshot of what is actually installed on the Thor, plus scripts to sync it back and forth.

## What's here

| Path | What it is |
|---|---|
| `store/ntdll-pr47-experimental-11.0-20261008/` | **Patched `ntdll.dll`** (pr47) — the one Overwatch launches with |
| `store/original-Proton_Experimental_ARM64-experimental-11.0-20261008-arm64-ntdll/` | Valve's original `ntdll.dll` from the same Proton build |
| `store/FEXCore-2610-d2rfix28-linux/` | d2rfix28 FEX build (`libwow64fex`, `libarm64ecfex` .dll/.so) |
| `patches/ntdll-pr47.bytediff` | Byte-level diff original → pr47 (161 bytes) |
| `config/desired.tsv` | DroidDeck's per-game wiring (full file, live copy) |
| `config/desired-2357570.tsv` | Just the Overwatch rows from it |
| `config/game-environment.json` | Per-game env vars (FEX TSO/SMC settings etc.), live copy |
| `config/reapplied.log` | DroidDeck's reapply log |
| `backups/ow-backup-151732/` | The pre-change backups from `/data/local/tmp/ow-backup-151732/` |
| `SHA256SUMS` | Hashes of everything under `store/` |

All `store/` hashes were verified against the device when pulled (2026-10-12).

## How it's wired on the device

Base path: `/data/user/0/com.antutu.benchmark.full/files/linuxfs/root/.local/share/droiddeck-components/`

DroidDeck reads `desired.tsv` before each launch and copies the listed store files into the Proton install.
For Overwatch it has one ntdll row:

```
2357570  Proton Experimental (ARM64)  experimental-11.0-20261008-arm64  ntdll  files/lib/wine/aarch64-windows/ntdll.dll  fb6022ab…392f  …/store/ntdll-pr47-experimental-11.0-20261008/…/ntdll.dll
```

…plus FEX rows pointing at `FEXCore-2610-d2rfix28-linux` for every Proton version, and dxvk 3.1.1 / vkd3d-proton 3.0a rows.

## The ntdll patch

`patches/ntdll-pr47.bytediff` (offsets are file offsets):

| File offset | Size | Section | Likely purpose |
|---|---|---|---|
| `0x188` | 2 B | PE header | checksum |
| `0x7a11c`, `0xcbccc`, `0xcc488`, `0xdfa6c` | 4 B each | `.text` | single arm64 instructions, presumably branches into the new code |
| `0xf30b0` | 159 B | `.text` | new code |
| `0x14b63b` | 3 B | `.rdata` | data/string tweak |

The source of pr47 isn't in this repo, only the built binary. If Proton Experimental updates and the
original ntdll is still byte-identical at those offsets, the patch can be re-applied:

```sh
scripts/bytediff.py apply path/to/new/original/ntdll.dll patches/ntdll-pr47.bytediff ntdll-patched.dll
```

It refuses if any original byte doesn't match, so a changed build fails loudly instead of producing a broken DLL.

## Scripts

Device defaults to serial `65636070`; override with `ANDROID_SERIAL=...`. Needs root (Magisk `su`).

- `scripts/verify.sh` — compare repo hashes with the device; show the active ntdll wiring. Read-only.
- `scripts/pull.sh` — refresh `store/` and `config/` from the device, regenerate `SHA256SUMS`.
- `scripts/push.sh` — install `store/` dirs to the device. `--config` also overwrites `desired.tsv` and
  `game-environment.json`. Whatever it replaces is saved to `/data/local/tmp/ow-push-<timestamp>/` first.
- `scripts/bytediff.py` — make/apply byte diffs.
- `scripts/release.sh VERSION` — tag and build `dist/overwatch-droid-VERSION.{tar.gz,zip}` (no `backups/`).

### Installing from a release archive

Unpack, plug in the Thor, then run `scripts/push.sh --config` from the unpacked folder (or plain `push.sh` to
leave the device's `desired.tsv` / `game-environment.json` alone).

### Rolling back to stock ntdll

Edit the `ntdll` row for `2357570` in `desired.tsv` so its hash/source point at the
`original-…-arm64-ntdll` store copy (`541403217f19…4046`), or remove the row.

## Notes

- `*.vdf` (Steam `config.vdf`, `localconfig.vdf`) are in `backups/` on disk but gitignored. They can contain
  login tokens and account data.
- `backups/ow-backup-151732/game-environment.json` differs from the live one: the backup had FEX TSO off and
  `FEX_SMCCHECKS=full`; the live config has TSO + vector TSO on and `FEX_SMCCHECKS=mtrack`.
- On the device the pr47 `ntdll.dll` is labelled `app_data_file:s0` without the app's MLS categories.
  `desired.tsv` has `s0:c164,c256,c512,c768`. It works as-is. `push.sh` labels files to match `desired.tsv`.
