# Overwatch Droid

I got Overwatch 2 running on my AYN Thor through DroidDeck, Proton Experimental (ARM64) and FEX, and wrapped
the whole setup into one install script so you can try it too.

[![Overwatch Droid final performance update](https://i.ytimg.com/vi/IrvZEAGfkqI/hqdefault.jpg)](https://www.youtube.com/watch?v=IrvZEAGfkqI)

▶ [Watch it running on the Thor](https://www.youtube.com/watch?v=IrvZEAGfkqI)

The installer does three things:

- Swaps Proton's `ntdll.dll` for a patched one that gets Overwatch past Blizzard's loader
- Installs a FEX build with fixes for Blizzard games, plus tuned FEX settings for Overwatch
- Sets Overwatch to Low, DirectX 12, 50% render scale, FSR off and a 90 fps cap

## Read this first

This is a community workaround, not an official fix, so a few honest warnings:

- **The patched `ntdll.dll` hasn't been reviewed, and I don't know who made it.** It's a small binary patch
  (161 bytes) that looks like a port of [proton-wine PR #47](https://github.com/GameNative/proton-wine/pull/47),
  not a build from its source. It goes into Proton itself, so every game you run on Proton Experimental (ARM64)
  uses it. It only changes what ARM64EC tells FEX about memory and CPU flags, so other games are unlikely to
  notice, and `bash install.sh --uninstall` puts the stock file back.
- **Play with discretion; your Blizzard account is your call.** This goes beyond official Proton and FEX. That
  said, people play Overwatch through Proton on the Steam Deck, where it's unofficially supported
  ([rated Playable](https://www.pcgamesn.com/overwatch-2/steam-deck)), its anti-cheat
  [works under Proton](https://www.gamingonlinux.com/itemdb/app/17974/overwatch-2), and bans are rare. Blizzard
  has even reversed them before: Linux players banned in 2018 for using Wine and DXVK got them
  [overturned as a false positive](https://www.phoronix.com/news/Blizzard-Banning-DXVK-Wine). Still, not many
  people have tried this exact setup, so a spare account is a good idea at first.
- **I've only tested it on my Thor** (DroidDeck 0.4.0, one Proton build). Other Snapdragon devices should work,
  but I haven't confirmed it.

The installer itself plays it safe. It only touches DroidDeck's app folder and `/data/local/tmp`, checks file
hashes before replacing anything, shows you what it'll change, asks first, and backs everything up.

## Before you start

You'll need:

- A **rooted** Android device (Magisk) with **USB debugging** on
- **[DroidDeck](https://github.com/Droid-Deck/DroidDeck)** (any variant) with Steam signed in
- **Proton Experimental (ARM64)** build `experimental-11.0-20261008-arm64`. The patch only fits this build.
- **Overwatch 2** installed and launched once with that Proton
- A **Mac or Linux** computer with `adb` and `python3`
  - Mac: `brew install android-platform-tools` (python3 comes with `xcode-select --install`)
  - Debian/Ubuntu: `sudo apt install adb python3`
  - Windows might work through WSL, but I haven't tried it.

## Install

1. Grab the newest zip from the [tags page](https://github.com/jeremiah0/OverwatchDroid/tags) and unzip it.
2. Plug in your device and run this from the unzipped folder:

   ```sh
   bash install.sh
   ```

   It'll find your device and DroidDeck, check everything, show what it's about to change and ask before
   doing anything. If DroidDeck is open it offers to close it. If Magisk pops up on the device, tap **Grant**.

3. Open DroidDeck and play Overwatch with Proton Experimental (ARM64).

If Steam updates or verifies Proton Experimental (ARM64), the stock `ntdll.dll` comes back. Just run the
installer again; it's always safe to rerun.

Other options: `--dry-run` shows the changes without making them, `--uninstall` puts the stock `ntdll.dll`
back, and `--yes` skips the questions. `bash scripts/verify.sh` shows what's installed right now.

## My settings

These are what I run on the Thor. In DroidDeck, open Settings under Play Steam; most take effect the next time
Steam starts.

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

Overwatch eats a lot of CPU through FEX, so give it every core. Frame generation doubles what's on screen for a
bit of GPU and a little input lag. I also used dxvk 3.1.1 and vkd3d-proton 3.0a.

The 90 fps cap is just a ceiling so it never holds the game back. Expect about 30 to 60 in matches. If it feels
choppy, a lower cap like 60 can be smoother. After installing, High Quality Upsampling under Options > Video
should say Default.

Overwatch only saves settings when you quit from its menu, so if it gets killed, changes are lost. Running the
installer again puts its settings back. The full list of what it sets is in [the details](docs/DETAILS.md).

## Tips

- **Close other apps first.** If Overwatch closes mid-match with no error, Android ran out of memory and killed
  DroidDeck (`adb logcat -d | grep lowmemorykiller` will show it). Browsers, YouTube, emulators and screen
  recording all eat memory.
- **Keep it cool.** The CPU sits at 90 to 95 °C in a match, so max out the fan and performance mode.
- **Turn off the Steam overlay** for Overwatch (Properties > General). It saves some memory and CPU.
- **Warm up shaders** by loading custom game code `929PJ` before you play, so effects don't stutter the
  first time you see them in a match.

## Troubleshooting

| Problem | Fix |
|---|---|
| `adb not found` | Install it (see [Before you start](#before-you-start)). |
| `no device found` | Turn on USB debugging in Developer options and use a data cable. |
| `the device hasn't allowed this computer yet` | Unlock the device and tap Allow on the USB debugging prompt. |
| `no root access` | In Magisk > Superuser, allow Shell. |
| `found several devices` / `several DroidDeck installs` | Pick one when asked. |
| `need Proton Experimental (ARM64) build …` | Your Proton is a different build. See [When Proton updates](#when-proton-updates). |
| Graphics were "skipped" | Launch Overwatch once, quit from its menu, then run the installer again. |
| Graphics went back to high | Overwatch was killed before it could save. Run the installer again. |
| Overwatch closes mid-match | Out of memory. See [Tips](#tips). |

## When Proton updates

The patch only fits `experimental-11.0-20261008-arm64`, so on a newer build the installer stops without
changing anything. You can try applying the patch to the new build yourself; see
[the ntdll patch](docs/DETAILS.md#the-ntdll-patch). Hopefully the fixes land upstream and this whole dance
goes away.

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

I made this together with **Claude Opus** (Anthropic's AI, through Claude Code), and every commit says so.

- **Me ([jeremiah0](https://github.com/jeremiah0)):** got Overwatch running on my Thor (the repo started as a
  snapshot of that setup), did all the testing on real hardware, like playing matches and checking what each
  setting really does (I caught that one value meant FSR 2.2, not 1.0), found the DroidDeck settings, the vector
  TSO tweak and the `929PJ` tip, and handled the commits and releases.
- **Claude:** wrote the scripts, edited and improved the README and changelog, and traced how DroidDeck handles
  components and per-game settings by reading its files and source. It also analysed the ntdll patch and traced
  the patch and the FEX build back to their sources.

Licenses for the bundled files are in [the details](docs/DETAILS.md#licenses).
