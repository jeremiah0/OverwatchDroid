# A few more setup options

Run these commands in the extracted folder inside **DroidDeck's Linux desktop**, with Overwatch closed. Python 3 is required. The normal setup changes graphics settings and keeps your selected Proton, FEX and driver.

## Graphics

| Profile | Frame cap | Render scale |
|---|---:|---:|
| `balanced` | 60 | 67% |
| `cool` | 30 | 50% |
| `performance` | 90 | 50% |

These are starting points, not expected FPS. Try `cool` if the phone gets hot or slows down during a match.

```sh
bash install.sh --profile cool
bash install.sh --profile balanced --renderer dx11
bash install.sh --profile performance --renderer dx12
```

The renderer stays as it is unless you choose one. DX11/DX12 still need a compatible driver. This tool doesn't add support for a GPU that DroidDeck can't run on.

## Find your settings or undo a change

```sh
bash install.sh --doctor
bash install.sh --prefix '/path/to/compatdata/2357570/pfx'
bash install.sh --settings '/path/to/Settings_v0.ini'
bash install.sh --restore '/backup/folder/printed/by/setup'
```

Setup looks for Steam and Battle.net installs, including external libraries. If nothing is found, launch Overwatch once and quit from its menu, or give setup the path yourself.

Restore stops if you have changed the settings since installing. Compare the saved backup with your current file before replacing it manually. Use `--help` for all options or `--yes` to skip confirmation.

## The original DLL/FEX patch

This only fits **Proton Experimental (ARM64), build `experimental-11.0-20261008-arm64`**. It affects every game using that Proton. Don't copy these files into a newer build.

Close Windows games and Battle.net, then preview the patch:

```sh
bash install.sh --legacy-runtime "$HOME/.local/share/Steam/steamapps/common/Proton Experimental (ARM64)" --dry-run
```

Repeat without `--dry-run` to install. Keep **bundled FEX** selected for that Proton in DroidDeck. Setup checks the files, backs up everything it replaces, and prints a `--restore-runtime` command to undo it. Graphics profiles are a separate step after Overwatch has saved its settings.

The old computer-and-rooted-phone method is still available:

```sh
bash install.sh --legacy
bash install.sh --legacy --uninstall
```

That older uninstall restores only the stock DLL, leaving FEX and graphics settings in place. See the [original guide](LEGACY.md) for requirements, patch provenance and the Thor settings.

## Switching to newer Proton

Select the newer Proton and its bundled FEX in DroidDeck. Review/reset old per-game `FEX_*` overrides there too. Newer FEX builds include Blizzard fixes, but the full Overwatch fix hasn't been verified in the newer runtime. Try launching before changing graphics; keep your working setup until you've tested the replacement.
