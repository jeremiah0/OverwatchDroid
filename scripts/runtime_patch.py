#!/usr/bin/env python3
"""Rootless, exact-build fallback for the original October Proton/FEX patch."""
import argparse
import importlib.util
import json
from pathlib import Path
import stat
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = load("setup", "setup.py")
payload = load("payload", "check-payload.py")
VERSION = "experimental-11.0-20261008-arm64"
STOCK = "541403217f19deed9cd984ebd59f2ec71e708421e135c9d254bbb908d86e4046"
PATCHED = "fb6022ab71709d6aa671e686b6d916e0aea30b77ce2be6279fd03e21e359392f"
NTDLL = "files/lib/wine/aarch64-windows/ntdll.dll"
FILES = {
    NTDLL: "ntdll-pr47-experimental-11.0-20261008/" + NTDLL,
    **{f"files/lib/wine/{arch}/{name}": f"FEXCore-2610-d2rfix28-linux/files/lib/wine/{arch}/{name}"
       for arch, names in (("aarch64-unix", ("libarm64ecfex.so", "libwow64fex.so")),
                           ("aarch64-windows", ("libarm64ecfex.dll", "libwow64fex.dll"))) for name in names},
}


def ensure_idle(proc=Path("/proc")):
    setup.ensure_game_closed(proc)
    for path in proc.glob("[0-9]*/cmdline"):
        try:
            args = path.read_bytes().split(b"\0")
        except OSError:
            continue
        names = [arg.replace(b"\\", b"/").rsplit(b"/", 1)[-1].lower() for arg in args]
        if any(name in (b"wine", b"wine64", b"wineserver", b"wine-preloader", b"wine64-preloader")
               or name.endswith(b".exe") for name in names):
            raise setup.SetupError("Close Windows games and launchers (including Battle.net) before changing Proton, then try again.")


def plan(proton):
    payload.verify(HERE.parent)
    version = (proton / "version").read_text().split()
    if len(version) != 2 or version[1] != VERSION:
        raise setup.SetupError(f"This fallback only fits {VERSION}. Your Proton was not changed.")
    checksum = setup.digest((proton / NTDLL).read_bytes())
    if checksum not in (STOCK, PATCHED):
        raise setup.SetupError("This ntdll.dll isn't the known stock or patched file. Verify Proton in Steam first.")
    changes = []
    for relative, source in FILES.items():
        target = proton / relative
        if target.is_symlink() or proton not in target.resolve().parents:
            raise setup.SetupError(f"Unexpected linked runtime file: {target}. Nothing changed.")
        before = target.read_bytes()
        after = (HERE.parent / "store" / source).read_bytes()
        if before != after:
            changes.append((relative, before, after, stat.S_IMODE(target.stat().st_mode)))
    return changes


def apply(proton, changes, state):
    for relative, before, _, _ in changes:
        if (proton / relative).read_bytes() != before:
            raise setup.SetupError("Proton changed during setup. Close Steam's downloads and try again.")
    state.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix="runtime-", dir=state))
    manifest = {"version": 1, "kind": "legacy-runtime", "proton": str(proton), "files": []}
    for n, (relative, before, after, mode) in enumerate(changes):
        setup.atomic_write(backup / str(n), before)
        manifest["files"].append({"path": relative, "backup": str(n), "before": setup.digest(before),
                                  "after": setup.digest(after), "mode": mode})
    setup.atomic_write(backup / "manifest.json", json.dumps(manifest, indent=2).encode())
    print(f"Runtime backup: {backup}", flush=True)
    written = []
    try:
        for relative, before, after, mode in changes:
            target = proton / relative
            if target.read_bytes() != before:
                raise setup.SetupError("Proton changed during setup. No further files will be replaced.")
            setup.atomic_write(target, after, mode)
            written.append((target, before, after, mode))
            if target.read_bytes() != after:
                raise setup.SetupError(f"Verification failed for {relative}")
    except BaseException:
        for target, before, after, mode in reversed(written):
            try:
                if target.read_bytes() != after:
                    print(f"{target} changed externally; keeping that version. Backup: {backup}", file=sys.stderr)
                    continue
                setup.atomic_write(target, before, mode)
            except OSError:
                print(f"Couldn't roll back {target}; use the runtime backup at {backup}.", file=sys.stderr)
        raise
    return backup


def read_restore(backup):
    meta = json.loads((backup / "manifest.json").read_text())
    if not isinstance(meta, dict) or meta.get("version") != 1 or meta.get("kind") != "legacy-runtime":
        raise setup.SetupError("This isn't a runtime backup from this installer.")
    proton = Path(meta["proton"])
    if not proton.is_absolute():
        raise setup.SetupError("Invalid runtime backup path.")
    changes, seen = [], set()
    for n, entry in enumerate(meta["files"]):
        relative = entry["path"]
        if relative not in FILES or relative in seen or entry["backup"] != str(n):
            raise setup.SetupError("Invalid runtime backup entry.")
        seen.add(relative)
        target = proton / relative
        if target.is_symlink() or proton not in target.resolve().parents:
            raise setup.SetupError("The runtime file path has changed; automatic restore stopped.")
        original = (backup / str(n)).read_bytes()
        current = target.read_bytes()
        if setup.digest(original) != entry["before"]:
            raise setup.SetupError("The runtime backup checksum doesn't match.")
        if setup.digest(current) not in (entry["before"], entry["after"]):
            raise setup.SetupError("Proton changed after this patch (possibly an update). Automatic restore stopped.")
        if current != original:
            changes.append((relative, current, original, stat.S_IMODE(target.stat().st_mode)))
    return proton, changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--proton", type=Path, help="exact October Proton directory inside DroidDeck's Linux desktop")
    group.add_argument("--restore", type=Path, help="runtime backup directory")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", "-y", action="store_true")
    parser.add_argument("--backup-dir", type=Path, default=Path.home() / ".local/share/overwatch-droid/backups")
    args = parser.parse_args()
    if args.restore:
        proton, changes = read_restore(args.restore.expanduser().resolve())
    else:
        proton = args.proton.expanduser().resolve()
        changes = plan(proton)
    if not changes:
        print("The requested runtime files are already in place. Nothing changed.")
        return
    print(f"Proton: {proton}\nFiles to {'restore' if args.restore else 'patch'}:")
    for relative, _, _, _ in changes:
        print("  " + relative)
    print("This affects EVERY game using this Proton. Keep its bundled FEX selected in DroidDeck.\n"
          "This is the original binary workaround, not a new build or a new GPU driver.")
    if args.dry_run:
        print("Preview only. No files or backups written.")
        return
    ensure_idle()
    if not setup.confirm(args, "Back up these files and continue?"):
        print("Cancelled. Nothing changed.")
        return
    ensure_idle()
    backup = apply(proton, changes, args.backup_dir.expanduser().resolve())
    print("Runtime files verified. Any FEX environment choices are managed in DroidDeck's per-game UI.")
    command = "bash " + setup.shlex.quote(str(HERE.parent / "install.sh")) + " --restore-runtime " + setup.shlex.quote(str(backup))
    print(f"Undo this operation:\n  {command}")


if __name__ == "__main__":
    try:
        main()
    except (setup.SetupError, OSError, ValueError, KeyError, TypeError) as error:
        sys.exit(f"Couldn't finish: {error}")
    except (EOFError, KeyboardInterrupt):
        sys.exit("Cancelled.")
