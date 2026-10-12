# Overwatch Droid

Gets Overwatch 2 (Steam app `2357570`) running on Android handhelds through DroidDeck + Proton Experimental (ARM64) + FEX.
Tested on an AYN Thor.

It sets up, for Overwatch only:

- a patched Wine `ntdll.dll` (pr47) for Proton Experimental (ARM64)
- the d2rfix28 FEX build, plus the FEX settings Overwatch runs with (TSO + vector TSO on, `FEX_SMCCHECKS=mtrack`)
- Overwatch's own graphics settings: **Low preset + DirectX 12**

Other games' settings are left alone.

## Install

You need:

- A **rooted** device (Magisk) with [DroidDeck](https://github.com/Droid-Deck/DroidDeck) set up and Steam signed in.
  Any variant works (standard, antutu, ludashi, pubg); the installer finds it.
- **Proton Experimental (ARM64)** build **`experimental-11.0-20261008-arm64`** installed in DroidDeck's Steam.
  The patch only fits this exact build; the installer checks and refuses anything else.
- Overwatch 2 installed and **launched once** (so its Wine prefix exists and the settings can be written)
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

## Stability: it's about memory

If Overwatch closes mid-match with no error, Android killed DroidDeck because the device ran out of memory.
It isn't a game crash, so Overwatch writes no error report. You can confirm it with
`adb logcat -d | grep lowmemorykiller`, which shows a line like `Kill '<droiddeck package>' … device is low on memory`.
On an 11 GB Thor this happened about 4–6 minutes into matches.

Things that help:

- **Low preset + DX12.** The installer writes these into Overwatch's `Settings_v0.ini`. Overwatch on this setup
  usually gets killed before it can save settings itself, which is also why in-game changes seem not to stick.
  Low textures matter most, because the GPU shares system RAM.
- **Close every other app before playing** (browsers, YouTube, emulators, other games, controller apps).
  Android kills them first under pressure, but many restart in the background and take the memory back.
- **Don't run adb root commands while playing.** Each `su` call starts the Magisk app (~100 MB).

### Recommended: warm up shaders before playing

Load the Overwatch 2 custom game **`929PJ`** before you play (join it by code from the Custom Games browser).
It pre-compiles shaders and loads hero abilities, which fixes most of the stuttering and frame drops
you'd otherwise hit the first time each effect shows up in a real match.

## Details

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

- Checks for root, finds your DroidDeck install, checks the exact Proton build, and that Proton's current
  `ntdll.dll` is either stock or already pr47
- Backs up everything it changes to `/data/local/tmp/ow-backup-<timestamp>/` on the device
- Writes the pr47 `ntdll.dll` **directly into Proton Experimental (ARM64)**
- Copies the store folders into `droiddeck-components/store/` and sets Overwatch's `ntdll` and `fex` rows in
  `desired.tsv`, and Overwatch's entry in `game-environment.json`. Nothing else in those files changes.
- Sets `GFXPresetLevel = "1"` (Low) and `GraphicsAPI = "Dx12"` under `[Render.13]` in Overwatch's
  `Documents/Overwatch/Settings/Settings_v0.ini`, keeping any other settings in that file
- Shows what's in effect afterwards (`scripts/verify.sh`)

### Uninstall

```sh
bash scripts/install.sh --uninstall
```

Puts Valve's stock `ntdll.dll` back into Proton and points Overwatch's ntdll row at it. FEX and the game
settings stay. To revert something else, copy it back from the `/data/local/tmp/ow-backup-<timestamp>/` folder.

### How DroidDeck wires it

DroidDeck keeps components in
`/data/user/0/<droiddeck package>/files/linuxfs/root/.local/share/droiddeck-components/`.
`desired.tsv` lists files to copy into each Proton install (columns: appid, Proton name, Proton version,
component, path, sha256, source). The `source` paths are inside DroidDeck's Linux root (`/root/...`), so the
same rows work for every variant.

DroidDeck regenerates `desired.tsv` from its own component list at times (seen at session start). That
**drops hand-added `ntdll` rows** and then deletes the store folders nothing points at. The `ntdll.dll`
already inside Proton is left alone, which is why the installer writes it there directly. A Steam update or
"verify files" on Proton Experimental (ARM64) brings back the stock file. After that, rerun the installer if
the build is still `experimental-11.0-20261008-arm64`. A newer build needs a new patch (see below).

### The ntdll patch

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

## What's in the repo

| Path | What it is |
|---|---|
| `store/ntdll-pr47-experimental-11.0-20261008/` | Patched `ntdll.dll` (pr47) |
| `store/original-Proton_Experimental_ARM64-experimental-11.0-20261008-arm64-ntdll/` | Valve's original `ntdll.dll` from the same build (for uninstall) |
| `store/FEXCore-2610-d2rfix28-linux/` | d2rfix28 FEX (`libwow64fex`, `libarm64ecfex` .dll/.so) |
| `config/desired-2357570.tsv` | Overwatch's `desired.tsv` rows |
| `config/game-environment.json` | Overwatch's FEX environment |
| `config/Settings_v0.ini` | Overwatch graphics settings the installer applies (Low + DX12) |
| `patches/ntdll-pr47.bytediff` | Byte-level diff original → pr47 (161 bytes) |
| `SHA256SUMS` | Hashes of everything under `store/` |

### Maintainer scripts

- `scripts/verify.sh` — show Proton's `ntdll.dll`, the store folders and the Overwatch rows on a device. Read-only.
- `scripts/pull.sh` — refresh `store/` and `config/` from a device, regenerate `SHA256SUMS`.
- `scripts/release.sh VERSION` — tag and build `dist/overwatch-droid-VERSION.{tar.gz,zip}`.
- `scripts/bytediff.py`, `scripts/owconfig.py`, `scripts/find-droiddeck.sh` — byte diffs, the config merges and DroidDeck detection used by the installer.
