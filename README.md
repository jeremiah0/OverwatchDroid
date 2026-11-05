# Overwatch Droid

A small setup helper for playing Overwatch through [DroidDeck](https://github.com/Droid-Deck/DroidDeck).
It started with a working AYN Thor setup. The new installer makes it easier to try sensible graphics settings on other phones and keeps a backup so you can go back.

**Start with current DroidDeck-Proton.** It now includes Blizzard-loader fixes in its bundled FEX, although the complete Wine-side Overwatch fix has not been verified in that runtime. The normal installer adjusts Overwatch's graphics; it leaves your Proton, FEX and GPU driver in place. The old October binary patch is still available as a separate [legacy option](docs/LEGACY.md).

[Watch the original Thor setup](https://www.youtube.com/watch?v=IrvZEAGfkqI)

## Get started on your phone

No Android root, USB cable or computer is needed for this path. Run it in **DroidDeck's Linux desktop**, not Termux or Android's ADB shell.

1. Update DroidDeck and its runtime from the [official project](https://github.com/Droid-Deck/DroidDeck/releases). Install a current **DroidDeck-Proton** through Components, select it for Overwatch, and use its bundled FEX rather than an old custom FEX override. See [migration](#coming-from-the-old-patch) if you used this patch before.
2. Launch Overwatch once and quit from its own menu. If it cannot reach the menu, resolve the runtime/driver issue first; graphics setup cannot replace a missing loader fix.
3. Download this repository's ZIP using **Code → Download ZIP**, extract it in the Linux desktop, then open that folder in Konsole. Run:

   ```sh
   bash install.sh
   ```

Choose a profile, review the changes, and type `y` to apply them. Setup prints the backup location and an undo command. It finds existing Steam and Battle.net settings, including Steam's registered libraries and DroidDeck's SD-card libraries. If it finds several installs, it asks which one you mean.

**The new installer has automated tests but still needs phone testing.** The original October setup was tested on the Thor. No new device compatibility or FPS improvement is claimed yet.

## Choose how you want to play

| Profile | Frame cap | Render scale | Good starting point for |
|---|---:|---:|---|
| `balanced` (default) | 60 | 67% | Everyday play |
| `cool` | 30 | 50% | Lower rendering load and sustained sessions |
| `performance` | 90 | 50% | Faster devices with active cooling |

These are low-graphics starting points, not benchmark results or promised frame rates. Your controls, audio, current graphics API, buffering and upscaling choices are preserved. Render scale is relative to your chosen display resolution; try 1280×720 first, then adjust after a practice match.

```sh
bash install.sh --profile cool
bash install.sh --profile balanced --renderer dx11
bash install.sh --profile performance --renderer dx12
```

The default is **keep your current renderer**. DX11 uses DXVK; DX12 uses vkd3d-proton. Test both only if your driver supports them. A profile doesn't add Vulkan features or install a driver.

For tuning, change one thing at a time. Compare the same practice scene after shader warm-up and again after ten minutes. Use real rendered FPS and frame pacing, with frame generation off for the comparison. If the phone gets slower as it heats up, try `cool` before increasing clocks. Leave FEX's memory-ordering defaults intact initially; the old vector-TSO-off tweak is not a universal stability recommendation.

## Which GPUs can I try?

| GPU | DroidDeck route | What this setup does |
|---|---|---|
| Adreno | Turnip, with support depending on the chip and driver | Keeps the driver and renderer; offers all three profiles |
| Mali / Immortalis | Experimental MaliBridge, Venus or matching PanVK driver pair | Keeps the working graphics stack; allows an explicit DX11 trial |
| Samsung Xclipse | Experimental RADV driver pair / system route | Does not apply Adreno-only settings |
| PowerVR | Experimental system-driver route | Does not apply Adreno-only settings |
| Unknown | Check the exact GPU and DroidDeck build | Keeps the renderer; never guesses a driver |

On November 5, 2026, the broader non-Adreno integration [PR #2029](https://github.com/Droid-Deck/DroidDeck/pull/2029) was still open and awaiting device validation. The [community non-Adreno guide](https://github.com/The412Banner/droiddeck-nonadreno-drivers) documents test builds and device-specific limitations. **Those reports do not establish Overwatch compatibility.** First get Steam rendering correctly on the matching graphics stack.

The installer identifies the GPU when `vulkaninfo` is available. This is informational, not a feature test. You can specify `--gpu mali`, `--gpu xclipse`, or `--gpu powervr` if detection is unavailable. It won't download experimental drivers automatically.

## Check, preview, undo

```sh
bash install.sh --doctor
bash install.sh --profile cool --dry-run
bash install.sh --restore '/path/printed/by/setup'
```

A dry run writes nothing. Every changed install saves the original file and its checksum before replacing it. Repeating an unchanged install makes no extra backup. Restore checks the backup and stops if you have edited your settings since installation, so it won't silently discard a newer save.

For a custom prefix or another Windows user:

```sh
bash install.sh --prefix '/path/to/compatdata/2357570/pfx'
bash install.sh --settings '/path/to/Settings_v0.ini'
```

Use `--yes` for unattended setup, with an explicit profile and location when needed. `--help` lists all options. Python 3 is required; if it is missing, install `python3` using your Linux desktop's package manager.

## Coming from the old patch

1. In Overwatch's DroidDeck profile, select current DroidDeck-Proton and its bundled FEX. Remove your old custom FEX selection and review/reset the old per-game `FEX_*` overrides through DroidDeck's UI. `--doctor` can flag Steam Overwatch's environment overrides, but does not remove them.
2. Try launching with the newer runtime before applying a graphics profile. The presence of upstream loader fixes is a reason to test it, not a guarantee that every Overwatch update works.
3. If you want to restore the old patched Proton too, the rooted computer command remains:

   ```sh
   bash install.sh --legacy --uninstall
   ```

That restores only the exact October `ntdll.dll`; it keeps the legacy FEX and settings. Never copy that DLL into a newer Proton. The modern setup does not automatically undo changes made by the old installer.

Need the original workaround for `experimental-11.0-20261008-arm64`? You can now apply its **DLL and FEX files without Android root** from DroidDeck's Linux desktop:

```sh
bash install.sh --legacy-runtime "$HOME/.local/share/Steam/steamapps/common/Proton Experimental (ARM64)" --dry-run
```

Close Windows games and Battle.net, then repeat without `--dry-run`. Keep **bundled FEX** selected for that Proton in DroidDeck. This checks the exact version and DLL hash, backs up all five replaced files, and verifies the result. If a write fails, it attempts to roll back. It prints a `--restore-runtime` command that restores both the DLL and the original FEX; restore refuses files changed by a later Proton update. This is the same old binary payload, not a new build, and it affects every game using this Proton. Other Proton versions are rejected.

Graphics profiles are a separate step: run `bash install.sh` after the game has saved its settings. FEX environment choices remain in DroidDeck's UI; start with TSO enabled and review the historical settings in the [legacy details](docs/DETAILS.md#fex-settings) if necessary.

The original computer route is still `bash install.sh --legacy` on a Mac/Linux computer with a rooted phone. Both routes check every bundled binary hash before applying it. Read the [legacy guide](docs/LEGACY.md) for the binary's provenance and limitations.

## If something doesn't work

| What you see | What to try |
|---|---|
| No settings found | Use DroidDeck's Linux desktop; launch and quit Overwatch once, or pass `--prefix`. |
| More than one install | Select one interactively, or pass `--prefix` / `--settings`. |
| Black screen before Steam opens | Check DroidDeck's GPU/driver setup first. These game settings cannot fix that. |
| Overwatch won't reach its menu | Check the selected Proton/FEX and launch log; don't apply an old DLL to a new build. |
| Game closes during play | Check DroidDeck's shared logs for memory pressure, driver errors or game crashes. Close other apps and try the lower-load profile. |
| Settings revert | Quit Overwatch from its menu before running setup, and check that you selected the prefix you actually launch. |
| Restore says settings changed | Compare the backup with your current file. Copy it manually only if you want to discard the later changes. |

[Research and source links](docs/RESEARCH-2026-11-05.md) · [Legacy technical details](docs/DETAILS.md)

## Credits

This only works because of other people's work. Thank you all <3

- **[Dmage22](https://github.com/Dmage22)** wrote the Wine fixes for Blizzard's protected loaders
  ([proton-wine #47](https://github.com/GameNative/proton-wine/pull/47)) and the d2rfix FEX builds
  ([FEX-D2](https://github.com/Dmage22/FEX-D2)) that make Overwatch start at all.
- **FrontMage and aanze** tracked down the FEX bugs behind Blizzard games in
  [FEX #5328](https://github.com/FEX-Emu/FEX/issues/5328).
- **[FEX-Emu](https://github.com/FEX-Emu/FEX)**, **[Valve's Proton](https://github.com/ValveSoftware/Proton)**,
  **[Wine](https://www.winehq.org/)**, **[GameNative](https://github.com/GameNative/proton-wine)**,
  **[DroidDeck](https://github.com/Droid-Deck/DroidDeck)**, **[DXVK](https://github.com/doitsujin/dxvk)**,
  **[vkd3d-proton](https://github.com/HansKristian-Work/vkd3d-proton)** and **[Mesa](https://mesa3d.org/)**'s
  Turnip driver for everything this stands on.

### Who made this

The original Thor patch and guide were made with **Claude Opus** (through Claude Code). The rootless setup, recovery tests and November compatibility research were developed with **OpenAI Codex**. Hardware testing described below belongs to the original Thor setup.

- **Me ([jeremiah0](https://github.com/jeremiah0)):** got Overwatch running on my Thor (the repo started as a
  snapshot of that setup), did all the testing on real hardware, like playing matches and checking what each
  setting really does, found the DroidDeck settings, the vector TSO tweak and the `929PJ` tip, and handled the commits and releases.
- **Claude:** wrote the scripts, edited and improved the README and changelog, and traced how DroidDeck handles
  components and per-game settings by reading its files and source. It also analysed the ntdll patch and traced
  the patch and the FEX build back to their sources.

Licenses for the bundled files are in [the details](docs/DETAILS.md#licenses).
