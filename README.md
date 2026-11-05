# Overwatch Droid

I got Overwatch running on my AYN Thor through [DroidDeck](https://github.com/Droid-Deck/DroidDeck) and put the setup here so you can try it too.

[Watch it running on the Thor](https://www.youtube.com/watch?v=IrvZEAGfkqI)

## Quick start

For a game that already launches, this sets up the graphics. No root or computer needed.

1. Launch Overwatch once, then quit from its menu.
2. Download this repo with **Code → Download ZIP** and unzip it in DroidDeck's Linux desktop.
3. Open that folder in Konsole and run:

   ```sh
   bash install.sh
   ```

Pick `balanced`, `cool`, or `performance`, then confirm. Your controls and sound settings stay as they are. The installer saves a backup and prints an undo command.

To preview the changes:

```sh
bash install.sh --dry-run
```

**Game won't launch?** The original DLL/FEX patch is still included, but only fits the October Proton build. See the [setup guide](docs/SETUP.md) for that patch, renderer choices and troubleshooting.

The original setup was tested on the Thor. The new installer and other GPUs still need phone testing; faster performance isn't guaranteed.

Thanks to **Dmage22**, the DroidDeck team and everyone behind Wine, Proton and FEX. Built with help from Claude and Codex. [Credits](docs/LEGACY.md#credits) · [Licenses](docs/DETAILS.md#licenses)
