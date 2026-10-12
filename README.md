# Overwatch Droid

Gets Overwatch 2 (Steam app `2357570`) running on Android handhelds through DroidDeck + Proton Experimental (ARM64) + FEX.
Tested on an AYN Thor.

It installs two things into DroidDeck, for Overwatch only:

- a patched Wine `ntdll.dll` (pr47) for Proton Experimental (ARM64)
- the d2rfix28 FEX build, plus the FEX settings Overwatch runs with (TSO + vector TSO on, `FEX_SMCCHECKS=mtrack`)

Other games' settings are left alone.

## Install

You need:

- A **rooted** device (Magisk) with [DroidDeck](https://github.com/Droid-Deck/DroidDeck) set up and Steam signed in.
  Any variant works (standard, antutu, ludashi, pubg); the installer finds it.
- **Proton Experimental (ARM64)** build **`experimental-11.0-20261008-arm64`** installed in DroidDeck's Steam.
  The patch only fits this exact build; the installer checks and refuses anything else.
- A Mac or Linux computer with `adb` and `python3` (on Windows, use WSL — untested)
- USB debugging on, with this computer authorized, and **root allowed for Shell** in Magisk

Then:

1. Download the latest release zip from the [Releases/Tags page](https://github.com/jeremiah0/OverwatchDroid/tags) and unzip it,
   or `git clone https://github.com/jeremiah0/OverwatchDroid.git`.
2. Close DroidDeck on the device.
3. Plug in the device and run, from the unpacked folder:

   ```sh
   bash scripts/install.sh --dry-run   # checks everything, changes nothing
   bash scripts/install.sh
   ```

4. In DroidDeck, run Overwatch 2 with **Proton Experimental (ARM64)**. The working setup also uses
   **dxvk 3.1.1** and **vkd3d-proton 3.0a**. Pick those in DroidDeck's components for Overwatch if you have them.

If more than one device is connected (or an emulator), pick one: `ANDROID_SERIAL=<serial> bash scripts/install.sh`.

### Which DroidDeck install it patches

DroidDeck ships the same app under several package names, each a separate install with its own data:

| Variant | Package |
|---|---|
| standard | `com.droiddeck.launcher` |
| antutu | `com.antutu.benchmark.full` |
| ludashi | `com.ludashi.benchmark` |
| pubg | `com.tencent.ig` |

The installer looks for DroidDeck's files rather than a package name, so it picks up whichever you
have (and ignores a real PUBG Mobile install). If you have more than one variant, it uses the one with the
required Proton build installed. If several have it, it asks you to choose:

```sh
DROIDDECK_PACKAGE=com.droiddeck.launcher bash scripts/install.sh
```

### What the installer does

- Checks for root, finds your DroidDeck install, checks the exact Proton build, and that Proton's current `ntdll.dll` is either stock or already pr47
- Backs up your `desired.tsv`, `game-environment.json`, and any store folders it replaces to
  `/data/local/tmp/ow-backup-<timestamp>/` on the device
- Copies the three store folders into `droiddeck-components/store/`
- In `desired.tsv`: replaces only Overwatch's `ntdll` and `fex` rows. In `game-environment.json`: replaces only Overwatch's entry
- Verifies the installed files by SHA-256

### Uninstall

```sh
bash scripts/install.sh --uninstall
```

Points Overwatch back at Valve's stock `ntdll.dll`. The d2rfix28 FEX rows stay. To fully revert,
copy the files from the `/data/local/tmp/ow-backup-<timestamp>/` folder the install printed back into place.

## What's in the repo

| Path | What it is |
|---|---|
| `store/ntdll-pr47-experimental-11.0-20261008/` | Patched `ntdll.dll` (pr47) |
| `store/original-Proton_Experimental_ARM64-experimental-11.0-20261008-arm64-ntdll/` | Valve's original `ntdll.dll` from the same build (for uninstall) |
| `store/FEXCore-2610-d2rfix28-linux/` | d2rfix28 FEX (`libwow64fex`, `libarm64ecfex` .dll/.so) |
| `patches/ntdll-pr47.bytediff` | Byte-level diff original → pr47 (161 bytes) |
| `config/desired-2357570.tsv` | Overwatch rows from the reference device's `desired.tsv` |
| `config/game-environment.json` | Reference device's per-game env vars |
| `SHA256SUMS` | Hashes of everything under `store/` |
| `backups/` | Reference device's pre-patch state (git only, not in release downloads) |

## How DroidDeck wires it

DroidDeck keeps components in
`/data/user/0/<droiddeck package>/files/linuxfs/root/.local/share/droiddeck-components/`.
Before each launch it reads `desired.tsv` (columns: appid, Proton name, Proton version, component, path, sha256, source)
and copies the listed store files into the Proton install. Overwatch's ntdll row:

```
2357570  Proton Experimental (ARM64)  experimental-11.0-20261008-arm64  ntdll  files/lib/wine/aarch64-windows/ntdll.dll  fb6022ab…392f  /root/.local/share/droiddeck-components/store/ntdll-pr47-experimental-11.0-20261008/…/ntdll.dll
```

The `source` paths are inside DroidDeck's Linux root (`/root/...`), so the same rows work for every variant.

## The ntdll patch

| File offset | Size | Section | Likely purpose |
|---|---|---|---|
| `0x188` | 2 B | PE header | checksum |
| `0x7a11c`, `0xcbccc`, `0xcc488`, `0xdfa6c` | 4 B each | `.text` | single arm64 instructions, presumably branches into the new code |
| `0xf30b0` | 159 B | `.text` | new code |
| `0x14b63b` | 3 B | `.rdata` | data/string tweak |

When Proton Experimental updates you can try re-applying it to the new build's stock `ntdll.dll`:

```sh
python3 scripts/bytediff.py apply path/to/stock/ntdll.dll patches/ntdll-pr47.bytediff ntdll-patched.dll
```

It refuses if any original byte doesn't match, which is likely on a new build, so a mismatch fails loudly instead of producing a broken DLL.

## Maintainer scripts

- `scripts/verify.sh` — compare repo hashes with a device; show the active Overwatch ntdll row. Read-only.
- `scripts/pull.sh` — refresh `store/` and `config/` from a device, regenerate `SHA256SUMS`.
- `scripts/release.sh VERSION` — tag and build `dist/overwatch-droid-VERSION.{tar.gz,zip}`.
- `scripts/bytediff.py`, `scripts/owconfig.py` — byte diffs and the config merge used by the installer.
