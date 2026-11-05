#!/usr/bin/env python3
"""Rootless Overwatch graphics setup, run inside DroidDeck's Linux desktop.

The current runtime owns Proton, FEX and graphics drivers. This tool only edits
Overwatch's settings, with a byte-for-byte backup before every changed install.
"""
import argparse
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

# -I excludes the script directory from sys.path; load only our adjacent helper.
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("owconfig", HERE / "owconfig.py")
owconfig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owconfig)
PROFILES = {
    "balanced": (60, 67, "a starting point for everyday play"),
    "cool": (30, 50, "less rendering work and a lower frame cap"),
    "performance": (90, 50, "more headroom on a fast, actively cooled device"),
}
GPU_CHOICES = ("auto", "adreno", "mali", "xclipse", "powervr", "unknown")
RELATIVE_SETTINGS = Path("Documents/Overwatch/Settings/Settings_v0.ini")


class SetupError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def discover(home=None, mounts=Path("/mnt")):
    """Bounded discovery: Steam libraries and existing Overwatch config only."""
    home = home or Path.home()
    roots = [home / ".local/share/Steam", home / ".steam/steam",
             home / ".steam/root", home / ".droiddeck-x64/.local/share/Steam"]
    roots += [mounts / "droiddeck-sd", mounts / "droiddeck-sd/x86-64"]
    roots += list((mounts / "droiddeck-lib").glob("*"))
    roots += [root / "x86-64" for root in (mounts / "droiddeck-lib").glob("*")]
    for root in roots[:]:
        vdf = root / "steamapps/libraryfolders.vdf"
        if vdf.is_file():
            for path in re.findall(r'"path"\s+"((?:\\.|[^"\\])*)"', vdf.read_text()):
                path = path.replace(r'\"', '"').replace("\\\\", "\\")
                if Path(path).is_absolute():
                    roots.append(Path(path))
    results = set()
    for root in set(roots):
        # Checking only the game's config also finds Battle.net and added-game
        # prefixes without assuming their generated Steam app IDs.
        for path in root.glob("steamapps/compatdata/*/pfx/drive_c/users/*/" + str(RELATIVE_SETTINGS)):
            if path.is_file():
                results.add(path.resolve())
    return sorted(results)


def prefix_settings(prefix):
    prefix = prefix.expanduser().resolve()
    if (prefix / "pfx/drive_c").is_dir():
        prefix /= "pfx"
    if not (prefix / "drive_c/users").is_dir():
        raise SetupError("That folder isn't a Wine prefix. Choose the pfx folder containing drive_c.")
    hits = [p.resolve() for p in (prefix / "drive_c/users").glob("*/" + str(RELATIVE_SETTINGS)) if p.is_file()]
    return sorted(set(hits))


def choose_settings(args):
    if args.settings:
        target = args.settings.expanduser().resolve()
        if target.name != "Settings_v0.ini" or not target.is_file():
            raise SetupError("Choose an existing Overwatch Settings_v0.ini file.")
        return target
    hits = prefix_settings(args.prefix) if args.prefix else discover()
    if not hits:
        raise SetupError("I couldn't find Overwatch's saved settings. Run this inside DroidDeck's Linux desktop.\n"
                         "Launch Overwatch once and quit from its menu, then try again. For another library or\n"
                         "Battle.net prefix, use --prefix '/path/to/pfx'. No files were changed.")
    if len(hits) == 1:
        return hits[0]
    print("I found more than one Overwatch install:")
    for n, hit in enumerate(hits, 1):
        print(f"  {n}. {hit}")
    if not sys.stdin.isatty() or args.yes:
        raise SetupError("Choose one explicitly with --prefix '/path/to/pfx' or --settings '/path/to/Settings_v0.ini'.")
    answer = input("Which install should I use? ").strip()
    if not answer.isdigit() or not 1 <= int(answer) <= len(hits):
        raise SetupError("No install selected. Run setup again when you're ready.")
    return hits[int(answer) - 1]


def gpu_family(text):
    text = text.lower()
    if any(word in text for word in ("adreno", "turnip")):
        return "adreno"
    if any(word in text for word in ("mali", "immortalis", "panvk", "panfrost")):
        return "mali"
    if "xclipse" in text:
        return "xclipse"
    if any(word in text for word in ("powervr", "rogue")):
        return "powervr"
    return "unknown"


def probe_gpu():
    if shutil.which("vulkaninfo"):
        try:
            result = subprocess.run(["vulkaninfo", "--summary"], capture_output=True, text=True,
                                    timeout=8, check=False)
            # Classify device names, not driver layers or optional software ICDs.
            names = re.findall(r"deviceName\s*=\s*(.+)", result.stdout)
            families = {gpu_family(name) for name in names} - {"unknown"}
            if len(families) == 1:
                return families.pop(), "; ".join(names)
        except (OSError, subprocess.TimeoutExpired):
            pass
    return "unknown", "GPU could not be identified; your current driver and renderer will be kept"


def ensure_game_closed(proc=Path("/proc")):
    for entry in proc.glob("[0-9]*/cmdline"):
        try:
            argv = entry.read_bytes().split(b"\0")
        except (OSError, PermissionError):
            continue
        # Inspect individual executable arguments, not a shell's command string.
        if any(arg.replace(b"\\", b"/").rsplit(b"/", 1)[-1].lower() == b"overwatch.exe" for arg in argv):
            raise SetupError("Overwatch is still running. Quit it from its menu, then try again.")


def preset_text(profile, renderer):
    fps, scale, _ = PROFILES[profile]
    base = (HERE.parent / "config/Settings_v0.ini").read_text()
    # The original Thor-specific renderer, upscaler and buffering choices are
    # deliberately not universal defaults. Existing values remain untouched.
    skip = {"GraphicsAPI", "HighQualityUpsample", "CpuForceSyncEnabled"}
    lines = [line for line in base.splitlines() if line.split("=", 1)[0].strip() not in skip]
    text = "\n".join(lines) + "\n"
    text = re.sub(r'DesiredFrameRate = "\d+"', f'DesiredFrameRate = "{fps}"', text)
    text = re.sub(r'MinWorldScale = "[\d.]+"', f'MinWorldScale = "{scale:.6f}"', text)
    if renderer != "keep":
        text += f'GraphicsAPI = "{renderer.capitalize()}"\n'
    return text


def atomic_write(path, data, mode=0o600):
    fd, name = tempfile.mkstemp(prefix=".overwatch-droid-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def apply_settings(path, before, after, state):
    # Refuse a race with the game or another setup; the original must still match.
    if path.read_bytes() != before:
        raise SetupError("Settings changed while setup was open. Quit Overwatch and run setup again.")
    state.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-"), dir=state))
    mode = stat.S_IMODE(path.stat().st_mode)
    atomic_write(backup / "Settings_v0.ini", before)
    manifest = {"version": 1, "target": str(path), "before_sha256": digest(before),
                "after_sha256": digest(after), "mode": mode}
    atomic_write(backup / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
    # Save backup and recovery information before replacing the one target.
    if path.read_bytes() != before:
        raise SetupError(f"Settings changed; no install applied. Backup: {backup}")
    atomic_write(path, after, mode)
    if path.read_bytes() != after:
        raise SetupError(f"Settings changed after writing. Quit the game and restore from {backup}")
    return backup


def confirm(args, question):
    if args.yes:
        return True
    if not sys.stdin.isatty():
        raise SetupError("Preview complete. Run in a terminal to confirm, or add --yes to apply this choice.")
    return input(question + " [y/N] ").strip().lower() in ("y", "yes")


def restore(args):
    backup = args.restore.expanduser().resolve()
    meta = json.loads((backup / "manifest.json").read_text())
    if not isinstance(meta, dict) or meta.get("version") != 1:
        raise SetupError("This backup uses an unsupported format.")
    path = Path(meta["target"])
    if not path.is_absolute() or path.name != "Settings_v0.ini":
        raise SetupError("This backup doesn't point to an Overwatch settings file.")
    original = (backup / "Settings_v0.ini").read_bytes()
    if digest(original) != meta["before_sha256"]:
        raise SetupError("The backup checksum doesn't match. Nothing was restored.")
    current = path.read_bytes()
    if current == original:
        print("Your original settings are already restored.")
        return
    if digest(current) != meta["after_sha256"]:
        raise SetupError("Your settings changed after this install. Automatic restore stopped to keep those edits.\n"
                         f"You can compare the current file with {backup / 'Settings_v0.ini'} and copy it manually.")
    print(f"Restore your previous settings to:\n  {path}")
    if args.dry_run:
        print("Preview only. Nothing changed.")
        return
    ensure_game_closed()
    if confirm(args, "Restore these settings?"):
        if path.read_bytes() != current:
            raise SetupError("Settings changed while waiting. Please try again with Overwatch closed.")
        atomic_write(path, original, stat.S_IMODE(path.stat().st_mode))
        print("Restored your previous settings. The backup is still available.")
    else:
        print("Cancelled. Your settings are unchanged.")


def main():
    parser = argparse.ArgumentParser(description="Set up Overwatch inside DroidDeck's Linux desktop, without root or ADB.",
                                     epilog="October binary fallback: --legacy-runtime PROTON_DIR (inside DroidDeck); --restore-runtime BACKUP to undo. Old computer/ADB path: --legacy --help.")
    parser.add_argument("--profile", choices=PROFILES, help="balanced (60 fps/67%%), cool (30/50%%), performance (90/50%%)")
    parser.add_argument("--renderer", choices=("keep", "dx11", "dx12"), default="keep", help="keep your current API (default), or choose one to test")
    parser.add_argument("--gpu", choices=GPU_CHOICES, default="auto", help="optional GPU hint; does not install a driver")
    location = parser.add_mutually_exclusive_group()
    location.add_argument("--prefix", type=Path, help="Wine pfx folder, including a Battle.net or external-library prefix")
    location.add_argument("--settings", type=Path, help="select one existing Settings_v0.ini directly")
    parser.add_argument("--dry-run", action="store_true", help="show the exact changes without writing anything")
    parser.add_argument("--doctor", action="store_true", help="check paths, GPU and current settings without changing files")
    parser.add_argument("--restore", type=Path, metavar="BACKUP", help="restore the settings from a specific backup folder")
    parser.add_argument("--backup-dir", type=Path, default=Path.home() / ".local/share/overwatch-droid/backups")
    parser.add_argument("-y", "--yes", action="store_true", help="apply the displayed choices without prompting")
    args = parser.parse_args()
    if args.restore and (args.doctor or args.prefix or args.settings or args.profile or args.renderer != "keep"):
        parser.error("--restore cannot be combined with install choices or --doctor")
    print("Overwatch Droid — let's get your settings ready.\n")
    if args.restore:
        restore(args)
        return
    gpu, detail = probe_gpu() if args.gpu == "auto" else (args.gpu, "your selection")
    print(f"GPU: {gpu} ({detail})")
    if gpu in ("mali", "xclipse", "powervr"):
        print("This GPU needs a compatible experimental DroidDeck build/driver. These settings alone cannot enable it.\n"
              "If Steam already renders correctly, DX11 is an option to test; DX12 is not forced.\n"
              "Unofficial community test builds and drivers (third-party, not reviewed by this project):\n"
              "  https://github.com/The412Banner/droiddeck-nonadreno-drivers")
    print("Use a current DroidDeck-Proton and its bundled FEX first; the October DLL/FEX files are not installed here.")
    path = choose_settings(args)
    print(f"Overwatch settings:\n  {path}")
    before = path.read_bytes()
    text = before.decode("utf-8-sig")
    if sum(line.strip() == "[Render.13]" for line in text.splitlines()) != 1:
        raise SetupError("The saved graphics format isn't recognized. Launch and quit Overwatch once; keep this file for inspection.")
    if args.doctor:
        for line in text.splitlines():
            if line.split("=", 1)[0].strip() in ("GraphicsAPI", "DesiredFrameRate", "MinWorldScale"):
                print("  " + line.strip())
        env = Path.home() / ".config/droiddeck/game-environment.json"
        if env.is_file():
            data = json.loads(env.read_text())
            if not isinstance(data, dict) or not isinstance(data.get("games", {}), dict):
                raise SetupError("DroidDeck's guest environment has an unexpected format. No files changed.")
            overrides = data.get("games", {}).get("2357570", {})
            if not isinstance(overrides, dict):
                raise SetupError("Overwatch's environment has an unexpected format. No files changed.")
            if any(key.startswith("FEX_") for key in overrides):
                print("Steam Overwatch has FEX overrides. Review/reset them in DroidDeck's per-game settings when migrating from the old patch.")
        ensure_game_closed()
        print("Check complete. No files changed. GPU detection is not a Vulkan feature or game-compatibility test.")
        return
    profile = args.profile or "balanced"
    if not args.profile and sys.stdin.isatty() and not args.yes and not args.dry_run:
        for name, (fps, scale, description) in PROFILES.items():
            print(f"  {name}: {fps} fps cap, {scale}% render scale — {description}")
        profile = input("Choose a profile [balanced]: ").strip().lower() or "balanced"
        if profile not in PROFILES:
            raise SetupError("Choose balanced, cool or performance. No files changed.")
    after = owconfig.render_settings(text, preset_text(profile, args.renderer)).encode("utf-8")
    print(f"\nPlan: {profile}; renderer: {args.renderer}. Frame caps are targets, not promised FPS.")
    print("Your controls, sound and unrelated settings stay as they are.")
    if after == before:
        print("These settings are already in place. Nothing to change.")
        return
    for line in difflib.unified_diff(text.splitlines(), after.decode().splitlines(), fromfile="your settings", tofile=profile, lineterm=""):
        print(line)
    if args.dry_run:
        print("\nPreview only. No files or backups were written.")
        return
    ensure_game_closed()
    if not confirm(args, "Save a backup and apply these settings?"):
        print("Cancelled. Your settings are unchanged.")
        return
    ensure_game_closed()
    backup = apply_settings(path, before, after, args.backup_dir.expanduser().resolve())
    print(f"\nAll set. Open Overwatch and try a practice match.\nBackup: {backup}")
    command = "bash " + shlex.quote(str(HERE.parent / "install.sh")) + " --restore " + shlex.quote(str(backup))
    print(f"To undo this install:\n  {command}")


if __name__ == "__main__":
    try:
        main()
    except (SetupError, OSError, ValueError, KeyError) as error:
        print(f"\nCouldn't finish: {error}", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
