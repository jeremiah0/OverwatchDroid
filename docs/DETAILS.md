# Overwatch Droid: the details

The nuts and bolts behind the [README](../README.md): exactly what the installer sets, how DroidDeck
handles it, what the ntdll patch changes, and what's in the repo.

## Graphics settings

These go in `Documents/Overwatch/Settings/Settings_v0.ini` in Overwatch's Wine prefix, mostly under `[Render.13]`.
Anything else in the file is kept. The values are the ones Overwatch saves itself for each option.

| In-game option | Setting | Value |
|---|---|---|
| Graphics preset | `GFXPresetLevel` | `1` (Low) |
| Graphics API | `GraphicsAPI` | `Dx12` |
| Render scale | `UseCustomWorldScale`, `MinWorldScale` | `1`, `50.000000` (50%) |
| High quality upsampling | `HighQualityUpsample` | `0` (Default, no FSR) |
| Frame rate cap | `UseCustomFrameRates`, `DesiredFrameRate` | `1`, `90` |
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

FSR is off because it costs GPU time every frame, and DroidDeck's Snapdragon GSR already sharpens the final
image. Reduce Buffering is off so the CPU can work on the next frame while the GPU draws this one, which helps
because FEX makes Overwatch CPU-bound. It costs a little input lag; turn it back on in Options > Video if you'd
rather have that back.

## FEX settings

Set for Overwatch only, in DroidDeck's per-game environment (`game-environment.json`).

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

## How it works

DroidDeck keeps components in `/data/user/0/<package>/files/linuxfs/root/.local/share/droiddeck-components/`.
`desired.tsv` there lists files to copy into each Proton install before a game launches.
The installer adds Overwatch's `ntdll` and `fex` rows to it and copies the files into `store/`.

DroidDeck rebuilds `desired.tsv` from its own state, which only knows FEX, DXVK and VKD3D, so it drops the
`ntdll` rows and deletes their store folders. It doesn't touch the `ntdll.dll` that's already in Proton, so the
installer writes it there directly too. That's why every game on that Proton gets it. A per-game ntdll
component has been proposed upstream in [DroidDeck #675](https://github.com/Droid-Deck/DroidDeck/issues/675).

The installer finds DroidDeck by its files, not its package name, so every variant works:

| Variant | Package |
|---|---|
| standard | `com.droiddeck.launcher` |
| antutu | `com.antutu.benchmark.full` |
| ludashi | `com.ludashi.benchmark` |
| pubg | `com.tencent.ig` |

Overrides for the installer: `ANDROID_SERIAL=<serial>` picks a device, `DROIDDECK_PACKAGE=<package>` picks a
DroidDeck install.

## The ntdll patch

pr47 changes 161 bytes of Valve's `ntdll.dll`:

| Offset | Size | Section | What it is |
|---|---|---|---|
| `0x188` | 2 B | PE header | checksum |
| `0x7a11c`, `0xcbccc`, `0xcc488`, `0xdfa6c` | 4 B each | `.text` | single instructions, likely jumps to the new code |
| `0xf30b0` | 159 B | `.text` | new code, including the name `__wine_arm64ec_extended_eflags` from PR #47 |
| `0x14b63b` | 3 B | `.rdata` | data |

To try it on a newer Proton build's stock `ntdll.dll`:

```sh
python3 scripts/bytediff.py apply path/to/stock/ntdll.dll patches/ntdll-pr47.bytediff ntdll-patched.dll
```

It stops if any of the original bytes don't match, which is likely on a different build.

## Files

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

- `scripts/verify.sh`: shows what's installed on a device. Changes nothing.
- `scripts/pull.sh`: copies the files from a device into the repo
- `scripts/release.sh VERSION`: tags a release and builds the zip
- `scripts/bytediff.py`, `scripts/owconfig.py`, `scripts/find-droiddeck.sh`, `scripts/env.sh`: used by the installer

## Licenses

| Files | License | Source |
|---|---|---|
| `store/*ntdll*/` | LGPL-2.1-or-later (Wine) | Valve's Proton Experimental (ARM64) `experimental-11.0-20261008-arm64`; the patch is in `patches/ntdll-pr47.bytediff` |
| `store/FEXCore-2610-d2rfix28-linux/` | MIT (FEX) | [Dmage22/FEX-D2 d2rfix28 build 37](https://github.com/Dmage22/FEX-D2/releases/tag/fexcore-2610-d2rfix28-37), commit `15a5bba`. The DLLs are byte-identical to that release. |
