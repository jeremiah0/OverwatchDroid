# Overwatch Droid

Patch for running Overwatch 2 on Android through DroidDeck, Proton Experimental (ARM64) and FEX. Tested on an AYN Thor.

The installer changes these for Overwatch only:

- Replaces Proton's `ntdll.dll` with the pr47 patched version
- Installs the d2rfix28 build of FEX and Overwatch's FEX settings, with vector TSO off
- Sets Overwatch's graphics to Low and DirectX 12

Other games aren't affected.

## Requirements

- Rooted Android device (Magisk), with Shell allowed root access
- [DroidDeck](https://github.com/Droid-Deck/DroidDeck) with Steam signed in. Any DroidDeck variant works.
- Proton Experimental (ARM64) build `experimental-11.0-20261008-arm64`. The patch only works on this build.
- Overwatch 2 installed and launched at least once
- A Mac or Linux computer with `adb` and `python3`. Windows might work through WSL but hasn't been tested.

## Install

1. Download the latest zip from the [tags page](https://github.com/jeremiah0/OverwatchDroid/tags) and unzip it.
2. Close DroidDeck.
3. Plug in the device and run this from the unzipped folder:

   ```sh
   bash scripts/install.sh --dry-run
   bash scripts/install.sh
   ```

   `--dry-run` shows what would change without changing anything.

4. Play Overwatch with Proton Experimental (ARM64). The setup this was tested on also used dxvk 3.1.1 and vkd3d-proton 3.0a.

If you have more than one device connected, add `ANDROID_SERIAL=<serial>` in front of the command.

To undo the ntdll patch:

```sh
bash scripts/install.sh --uninstall
```

Everything the installer changes gets backed up on the device to `/data/local/tmp/ow-backup-<timestamp>/`.

## DroidDeck settings

These are the settings on the Thor this was tested on. Open DroidDeck, then pull up Settings under Play Steam.
Most of these take effect the next time you start Steam.

| Where | Setting | Value |
|---|---|---|
| Session > Performance | Override Steam's core choice | Off |
| Session > Performance | Game cores | All (cpu0 to cpu7) |
| Session > Performance | Hold the GPU at its top clock | On |
| Session > Performance | gamescope: realtime GPU queue | On |
| Session > Performance | droiddeck-ntsync (experimental) | On |
| Settings sheet | Upscaler | Snapdragon GSR (quality), sharpness 75% |
| Settings sheet | Frame generation | Win-FG 2× |
| Display | Resolution | 1280x720 |
| Components | GPU driver | Mesa Turnip v26.3.0-20261012 |

Overwatch uses a lot of CPU through FEX, so give it every core. Frame generation doubles the 30 fps cap to 60 on screen,
at the cost of some GPU and a little input lag.

## Overwatch settings

The installer adds these to `Documents/Overwatch/Settings/Settings_v0.ini` in Overwatch's Wine prefix, under `[Render.13]`.
Anything else in that file is kept. These are the values Overwatch itself saves for each option.

| In-game option | Setting | Value |
|---|---|---|
| Graphics preset | `GFXPresetLevel` | `1` (Low) |
| Graphics API | `GraphicsAPI` | `Dx12` |
| Render scale | `UseCustomWorldScale`, `MinWorldScale` | `1`, `50.000000` (50%) |
| High quality upsampling | `HighQualityUpsample` | `1` (meant to be AMD FSR 1.0) |
| Frame rate cap | `UseCustomFrameRates`, `DesiredFrameRate` | `1`, `30` |
| Texture quality | `TextureDetail` | `1` (Low) |
| Model detail | `ModelQuality` | `1` (Low) |
| Shader quality | `ShaderQuality` | `1` (Low) |
| Lighting quality | `LightQuality` | `0` (Low) |
| Effects detail | `EffectsQuality` | `1` (Low) |
| Shadow detail | `DirectionalShadowDetail` | `1` (Low) |
| Local reflections | `LocalReflections` | `0` (Off) |
| Anti-alias quality | `AADetail` | `0` (Off) |
| Texture filtering | `MaxAnisotropy` | `1` |

After installing, check Options > Video > Graphics Quality > High Quality Upsampling. It should say AMD FSR 1.0.
If it doesn't, pick AMD FSR 1.0 and quit from Overwatch's menu. FSR 2.2 costs more on this GPU.

Overwatch only saves settings when you quit from its menu. If the game gets killed or you close DroidDeck,
changes are lost. Running the installer again puts the values above back.

## FEX settings

The installer sets these for Overwatch only, in DroidDeck's per-game environment (`game-environment.json`).

| Setting | Value | What it does |
|---|---|---|
| `FEX_TSOENABLED` | `1` | Keeps x86 memory ordering. Overwatch needs it. |
| `FEX_VECTORTSOENABLED` | `0` | Skips memory ordering for SIMD loads and stores. Saves CPU. |
| `FEX_SMCCHECKS` | `mtrack` | Detects self-modifying code by tracking memory writes |
| `FEX_MULTIBLOCK` | `1` | Translates bigger chunks of code at once |
| `FEX_X87REDUCEDPRECISION` | `1` | Faster x87 floating point |

If you get crashes or glitches that started after installing, turn vector TSO back on (`1`) in DroidDeck's
per-game settings for Overwatch.

DroidDeck keeps a master copy of this file in its app folder and copies it into the Linux root at every
session start, so the installer writes both. Editing only the copy in the Linux root gets undone.

## Tips

**Close other apps before playing.** If Overwatch closes mid-match without an error, Android ran out of memory and killed DroidDeck.
You can check with `adb logcat -d | grep lowmemorykiller`. Low settings and closing background apps
(browser, YouTube, emulators, other games) fix most of it. Screen recording uses memory too.

**Keep it cool.** The CPU runs at 90 to 95 °C in a match. Set the fan and performance mode to max.

**Turn off the Steam overlay for Overwatch.** In Steam: Overwatch > Properties > General. It saves some memory and CPU.

**Warm up shaders.** Before playing, load custom game code `929PJ`. It compiles shaders and loads hero abilities
so you don't get stutters or slow texture loading the first time you see each effect in a match.

## DroidDeck variants

DroidDeck comes in a few versions with different package names. Each is a separate install.

| Variant | Package |
|---|---|
| standard | `com.droiddeck.launcher` |
| antutu | `com.antutu.benchmark.full` |
| ludashi | `com.ludashi.benchmark` |
| pubg | `com.tencent.ig` |

The installer finds DroidDeck by its files, not its package name. If you have more than one with the right Proton build, pick one:

```sh
DROIDDECK_PACKAGE=com.droiddeck.launcher bash scripts/install.sh
```

## How it works

DroidDeck keeps components in `/data/user/0/<package>/files/linuxfs/root/.local/share/droiddeck-components/`.
`desired.tsv` there lists files to copy into each Proton install before a game launches.
The installer adds Overwatch's `ntdll` and `fex` rows to it and copies the files into `store/`.

DroidDeck sometimes rewrites `desired.tsv` and removes the `ntdll` rows, then deletes their store folders.
It doesn't touch the `ntdll.dll` that's already in Proton, so the installer also writes it there directly.
Per-game environment variables have two copies: `files/game-environment.json` in DroidDeck's app folder is the
master, and `linuxfs/root/.config/droiddeck/game-environment.json` is overwritten from it at session start.
If Steam updates or verifies Proton Experimental (ARM64), the stock file comes back and you need to run the installer again.

## The ntdll patch

pr47 changes 161 bytes of Valve's `ntdll.dll`:

| Offset | Size | Section | What it is |
|---|---|---|---|
| `0x188` | 2 B | PE header | checksum |
| `0x7a11c`, `0xcbccc`, `0xcc488`, `0xdfa6c` | 4 B each | `.text` | single instructions, likely jumps to the new code |
| `0xf30b0` | 159 B | `.text` | new code |
| `0x14b63b` | 3 B | `.rdata` | data |

When Proton updates you can try applying it to the new stock `ntdll.dll`:

```sh
python3 scripts/bytediff.py apply path/to/stock/ntdll.dll patches/ntdll-pr47.bytediff ntdll-patched.dll
```

It stops if any of the original bytes don't match, which is likely on a different build.

## Files

| Path | Contents |
|---|---|
| `store/ntdll-pr47-experimental-11.0-20261008/` | Patched `ntdll.dll` |
| `store/original-Proton_Experimental_ARM64-experimental-11.0-20261008-arm64-ntdll/` | Valve's original `ntdll.dll`, used by uninstall |
| `store/FEXCore-2610-d2rfix28-linux/` | d2rfix28 FEX |
| `config/desired-2357570.tsv` | Overwatch's `desired.tsv` rows |
| `config/game-environment.json` | Overwatch's FEX settings |
| `config/Settings_v0.ini` | Graphics settings the installer applies |
| `patches/ntdll-pr47.bytediff` | Byte diff from original to pr47 |
| `SHA256SUMS` | Hashes of the files in `store/` |

Scripts:

- `scripts/install.sh`: install, `--dry-run`, `--uninstall`
- `scripts/verify.sh`: shows what's installed on a device. Doesn't change anything.
- `scripts/pull.sh`: copies the files from a device into the repo
- `scripts/release.sh VERSION`: tags a release and builds the zip
- `scripts/bytediff.py`, `scripts/owconfig.py`, `scripts/find-droiddeck.sh`: used by the installer
