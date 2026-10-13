# Overwatch Droid

Run Overwatch 2 on Android with DroidDeck, Proton Experimental (ARM64) and FEX. Tested on an AYN Thor.

One command sets up Overwatch:

- Replaces Proton's `ntdll.dll` with the pr47 patched version
- Installs the d2rfix28 build of FEX with Overwatch's FEX settings (TSO on, vector TSO off)
- Sets Overwatch's graphics to Low, DirectX 12, 50% render scale, FSR off and a 30 fps cap

The FEX build and settings and the graphics settings apply to Overwatch only. The patched `ntdll.dll` goes into
Proton Experimental (ARM64) itself, so every game you run with that Proton uses it. The
[patch](https://github.com/GameNative/proton-wine/pull/47) only changes what ARM64EC tells FEX about memory
mappings and CPU flags, so other games are unlikely to notice. If one misbehaves, `bash install.sh --uninstall`
puts the stock file back. Every file the installer replaces is backed up on the device first.

## Read this first

This is a community workaround, not an official fix. Know these before you try it:

- **The patched `ntdll.dll` hasn't been reviewed.** It's a 161-byte binary patch to Valve's file, adding about 160 bytes
  of code. It looks like a port of [proton-wine PR #47](https://github.com/GameNative/proton-wine/pull/47)'s
  ntdll changes, but it isn't built from that PR's source, and its origin isn't known. It runs inside every
  game on Proton Experimental (ARM64). The exact bytes it changes are in `patches/ntdll-pr47.bytediff`.
- **Your Blizzard account is at your own risk.** Overwatch has anti-cheat, and this runs it under an emulator
  with a modified system DLL. No bans are known, but very few people have tried it. Consider a spare account first.
- **It's only been tested on one device:** an AYN Thor with DroidDeck 0.4.0 and one Proton build. Other
  Snapdragon devices should work, but nobody has confirmed it, and the recommended settings are tuned for the Thor.

The installer itself is careful. It only writes inside DroidDeck's app folder and `/data/local/tmp`, refuses
to run unless the Proton build and `ntdll.dll` match known hashes, shows what it will change and asks first,
and backs up everything it replaces.

## Before you start

You need:

- A **rooted** Android device (Magisk) with **USB debugging** on
- **[DroidDeck](https://github.com/Droid-Deck/DroidDeck)** (any variant) with Steam signed in
- **Proton Experimental (ARM64)** build `experimental-11.0-20261008-arm64`. The patch only works on this build.
- **Overwatch 2** installed and launched once with that Proton, so its settings file exists
- A **Mac or Linux** computer with `adb` and `python3`:
  - Mac: `brew install android-platform-tools` (python3 comes with `xcode-select --install`)
  - Debian/Ubuntu: `sudo apt install adb python3`
  - Windows might work through WSL but hasn't been tested.

## Install

1. Download the zip for the newest version from the [tags page](https://github.com/jeremiah0/OverwatchDroid/tags) and unzip it.
2. Plug in the device and run this from the unzipped folder:

   ```sh
   bash install.sh
   ```

   The installer finds your device and DroidDeck, checks the Proton build, shows what it will change and asks
   before doing anything. If DroidDeck is open it offers to close it. If Magisk asks on the device, tap **Grant**.

3. Open DroidDeck and play Overwatch with Proton Experimental (ARM64). The tested setup also used
   dxvk 3.1.1 and vkd3d-proton 3.0a.

Then set the [recommended settings](#recommended-settings) below.

**Run it again** whenever Steam updates or verifies Proton Experimental (ARM64), since that puts the stock
`ntdll.dll` back. Running it again is always safe.

Other options:

| Command | What it does |
|---|---|
| `bash install.sh --dry-run` | Show the exact changes without changing anything |
| `bash install.sh --uninstall` | Put Valve's stock `ntdll.dll` back. FEX and graphics settings are left as they are. |
| `bash install.sh --yes` | Don't ask questions (for scripts) |
| `bash scripts/verify.sh` | Show what's installed right now. Changes nothing. |

Backups go to `/data/local/tmp/ow-backup-<timestamp>/` on the device.

## Recommended settings

### DroidDeck

These are the settings on the tested Thor. Open DroidDeck, then open Settings under Play Steam.
Most of them take effect the next time you start Steam.

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

Overwatch uses a lot of CPU through FEX, so give it every core. Frame generation doubles the 30 fps cap to
60 on screen, at the cost of some GPU and a little input lag.

### In game

The installer turns High Quality Upsampling off (Default). FSR costs GPU time on every frame, and DroidDeck's
Snapdragon GSR already sharpens the final image. It also turns Reduce Buffering off, which lets the CPU work
on the next frame while the GPU draws this one. That helps because FEX makes Overwatch CPU-bound, at the cost
of a little input lag. If you'd rather have the lag back down, turn Reduce Buffering on in Options > Video.

After installing, Options > Video > Graphics Quality > High Quality Upsampling should say Default.

Overwatch only saves settings when you quit from its menu. If the game gets killed or you close DroidDeck,
changes are lost. Running the installer again puts its graphics settings back.

<details>
<summary>Graphics settings the installer applies</summary>

These go in `Documents/Overwatch/Settings/Settings_v0.ini` in Overwatch's Wine prefix, mostly under `[Render.13]`.
Anything else in the file is kept. The values are the ones Overwatch saves for each option.

| In-game option | Setting | Value |
|---|---|---|
| Graphics preset | `GFXPresetLevel` | `1` (Low) |
| Graphics API | `GraphicsAPI` | `Dx12` |
| Render scale | `UseCustomWorldScale`, `MinWorldScale` | `1`, `50.000000` (50%) |
| High quality upsampling | `HighQualityUpsample` | `0` (Default, no FSR) |
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
| Reduce buffering | `CpuForceSyncEnabled` | `0` (Off) |
| Intro video | `ShowIntro` in `[Cinematics.1]` | `0` (skipped) |

</details>

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

**Close other apps before playing.** If Overwatch closes mid-match without an error, Android ran out of memory
and killed DroidDeck. You can check with `adb logcat -d | grep lowmemorykiller`. Low settings and closing
background apps (browser, YouTube, emulators, other games) fix most of it. Screen recording uses memory too.

**Keep it cool.** The CPU runs at 90 to 95 °C in a match. Set the fan and performance mode to max.

**Turn off the Steam overlay for Overwatch.** In Steam: Overwatch > Properties > General. It saves some memory and CPU.

**Warm up shaders.** Before playing, load custom game code `929PJ`. It compiles shaders and loads hero abilities,
so you don't get stutters or slow texture loading the first time you see each effect in a match.

## Troubleshooting

| Problem | Fix |
|---|---|
| `adb not found` | Install it (see [Before you start](#before-you-start)). |
| `no device found` | Turn on USB debugging in Developer options and use a data cable. |
| `the device hasn't allowed this computer yet` | Unlock the device and tap Allow on the USB debugging prompt. |
| `no root access` | In Magisk > Superuser, allow Shell. |
| `found several devices` / `several DroidDeck installs` | Pick one when asked, or set `ANDROID_SERIAL=<serial>` or `DROIDDECK_PACKAGE=<package>` in front of the command. |
| `need Proton Experimental (ARM64) build …` | Your Proton is a different build. See [When Proton updates](#when-proton-updates). |
| Graphics were "skipped" | Launch Overwatch once, quit from its menu, then run the installer again. |
| Graphics settings went back to high | Overwatch was killed before it could save. Run the installer again. |
| Overwatch closes mid-match | Out of memory. See [Tips](#tips). |

DroidDeck variants have different package names:

| Variant | Package |
|---|---|
| standard | `com.droiddeck.launcher` |
| antutu | `com.antutu.benchmark.full` |
| ludashi | `com.ludashi.benchmark` |
| pubg | `com.tencent.ig` |

## When Proton updates

The patched `ntdll.dll` only fits Proton Experimental (ARM64) `experimental-11.0-20261008-arm64`.
On a newer build the installer stops without changing anything.

You can try applying the patch to the new build's stock `ntdll.dll` yourself:

```sh
python3 scripts/bytediff.py apply path/to/stock/ntdll.dll patches/ntdll-pr47.bytediff ntdll-patched.dll
```

It stops if any of the original bytes don't match, which is likely on a different build.

## How it works

DroidDeck keeps components in `/data/user/0/<package>/files/linuxfs/root/.local/share/droiddeck-components/`.
`desired.tsv` there lists files to copy into each Proton install before a game launches.
The installer adds Overwatch's `ntdll` and `fex` rows to it and copies the files into `store/`.
It finds DroidDeck by its files, not its package name, so every variant works.

DroidDeck sometimes rewrites `desired.tsv` and removes the `ntdll` rows, then deletes their store folders.
It doesn't touch the `ntdll.dll` that's already in Proton, so the installer also writes it there directly.

pr47 changes 161 bytes of Valve's `ntdll.dll`:

| Offset | Size | Section | What it is |
|---|---|---|---|
| `0x188` | 2 B | PE header | checksum |
| `0x7a11c`, `0xcbccc`, `0xcc488`, `0xdfa6c` | 4 B each | `.text` | single instructions, likely jumps to the new code |
| `0xf30b0` | 159 B | `.text` | new code |
| `0x14b63b` | 3 B | `.rdata` | data |

### Files

| Path | Contents |
|---|---|
| `install.sh` | Installer (runs `scripts/install.sh`) |
| `store/ntdll-pr47-experimental-11.0-20261008/` | Patched `ntdll.dll` |
| `store/original-Proton_Experimental_ARM64-experimental-11.0-20261008-arm64-ntdll/` | Valve's original `ntdll.dll`, used by uninstall |
| `store/FEXCore-2610-d2rfix28-linux/` | d2rfix28 FEX |
| `config/desired-2357570.tsv` | Overwatch's `desired.tsv` rows |
| `config/game-environment.json` | Overwatch's FEX settings |
| `config/Settings_v0.ini` | Graphics settings the installer applies |
| `patches/ntdll-pr47.bytediff` | Byte diff from original to pr47 |
| `SHA256SUMS` | Hashes of the files in `store/` |

Maintainer scripts:

- `scripts/pull.sh`: copies the files from a device into the repo
- `scripts/release.sh VERSION`: tags a release and builds the zip
- `scripts/bytediff.py`, `scripts/owconfig.py`, `scripts/find-droiddeck.sh`, `scripts/env.sh`: used by the installer

## Credits

This only works because of other people's work. Thank you all <3

- **[Dmage22](https://github.com/Dmage22)** wrote the Wine fixes for Blizzard's protected loaders
  ([GameNative/proton-wine #47](https://github.com/GameNative/proton-wine/pull/47)) and the d2rfix FEX builds
  ([Dmage22/FEX-D2](https://github.com/Dmage22/FEX-D2)) that make Overwatch 2 start at all.
- **FrontMage and aanze** tracked down the FEX bugs behind Blizzard games in
  [FEX-Emu/FEX #5328](https://github.com/FEX-Emu/FEX/issues/5328), which the d2rfix fixes build on.
- **[FEX-Emu](https://github.com/FEX-Emu/FEX)** for the x86 emulator everything runs on.
- **[Valve](https://github.com/ValveSoftware/Proton)** for Proton and its ARM64 builds, and the
  **[Wine](https://www.winehq.org/)** project underneath it.
- **[GameNative](https://github.com/GameNative/proton-wine)** for the proton-wine fork the ntdll fixes target.
- **[DroidDeck](https://github.com/Droid-Deck/DroidDeck)** for bringing Steam and Proton to Android.
- **[DXVK](https://github.com/doitsujin/dxvk)**, **[vkd3d-proton](https://github.com/HansKristian-Work/vkd3d-proton)**
  and **[Mesa](https://mesa3d.org/)**'s Turnip driver for the graphics stack.

Licenses of the bundled files:

| Files | License | Source |
|---|---|---|
| `store/*ntdll*/` | LGPL-2.1-or-later (Wine) | Valve's Proton Experimental (ARM64) `experimental-11.0-20261008-arm64`; the patch is in `patches/ntdll-pr47.bytediff` |
| `store/FEXCore-2610-d2rfix28-linux/` | MIT (FEX) | [Dmage22/FEX-D2 d2rfix28 build 37](https://github.com/Dmage22/FEX-D2/releases/tag/fexcore-2610-d2rfix28-37), commit `15a5bba`. The DLLs are byte-identical to that release. |
