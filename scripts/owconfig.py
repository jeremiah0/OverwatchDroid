#!/usr/bin/env python3
"""Edit DroidDeck config for Overwatch without touching other games.

  owconfig.py merge DEVICE_TSV REPO_TSV DEVICE_ENV REPO_ENV OUT_DIR "STORE_DIR ..."
      Replace the device's Overwatch ntdll/fex rows with the repo's, and the
      device's Overwatch entry in game-environment.json with the repo's.
  owconfig.py stock-ntdll DEVICE_TSV OUT_TSV STOCK_HASH STOCK_SOURCE
      Point any Overwatch ntdll rows at Valve's original ntdll.dll.
  owconfig.py env DEVICE_ENV REPO_ENV OUT_ENV
      Just the game-environment.json part of merge, for DroidDeck's master copy.
  owconfig.py settings DEVICE_INI REPO_INI OUT_INI
      Overwatch's Settings_v0.ini: set the repo's keys (Low preset, DX12) and keep
      every other line of the device's file. Creates it if the device has none.

desired.tsv columns: appid, proton name, proton version, component, path, sha256, source.
"""
import json
import os
import sys
from pathlib import Path

APPID = "2357570"
COMPONENTS = {"ntdll", "fex"}


def read_lines(path):
    if not os.path.exists(path):
        return []
    lines = Path(path).read_text().splitlines()
    return [l for l in lines if l.strip()]


def is_ours(fields):
    return len(fields) >= 7 and fields[0] == APPID and fields[3] in COMPONENTS


def merge(dev_tsv, repo_tsv, dev_env, repo_env, out_dir, store_dirs):
    store_dirs = store_dirs.split()
    ours = [l for l in read_lines(repo_tsv)
            if is_ours(l.split("\t")) and any(f"/store/{d}/" in l for d in store_dirs)]
    kept = [l for l in read_lines(dev_tsv) if not is_ours(l.split("\t"))]
    with open(os.path.join(out_dir, "desired.tsv"), "w") as f:
        f.write("\n".join(kept + ours) + "\n")

    merge_env(dev_env, repo_env, os.path.join(out_dir, "game-environment.json"))

    print(f"desired.tsv: kept {len(kept)} rows, set {len(ours)} Overwatch ntdll/fex rows")


def merge_env(dev_env, repo_env, out_env):
    # An absent file is fine; a damaged existing file must never be replaced by {}.
    text = Path(dev_env).read_text() if os.path.exists(dev_env) else ""
    env = json.loads(text) if text.strip() else {}
    if not isinstance(env, dict) or env.get("version", 1) != 1:
        raise ValueError("Unsupported game-environment.json; no changes written")
    env.setdefault("version", 1)
    env.setdefault("shared", {})
    games = env.setdefault("games", {})
    if not isinstance(games, dict) or not isinstance(games.get(APPID, {}), dict):
        raise ValueError("Invalid per-game environment; no changes written")
    games.setdefault(APPID, {}).update(json.loads(Path(repo_env).read_text())["games"][APPID])
    with open(out_env, "w") as f:
        json.dump(env, f, separators=(",", ":"))


def stock_ntdll(dev_tsv, out_tsv, stock_hash, stock_source):
    out, changed = [], 0
    for l in read_lines(dev_tsv):
        fields = l.split("\t")
        if len(fields) >= 7 and fields[0] == APPID and fields[3] == "ntdll":
            fields[5], fields[6] = stock_hash, stock_source
            changed += 1
        out.append("\t".join(fields))
    with open(out_tsv, "w") as f:
        f.write("".join(l + "\n" for l in out))
    if changed:
        print(f"desired.tsv: pointed {changed} Overwatch ntdll row(s) at the stock ntdll.dll")
    else:
        print("desired.tsv: no Overwatch ntdll rows, left as is")


def render_settings(text, preset):
    def parse(text):
        section, out = None, {}
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line
            elif "=" in line and section:
                out.setdefault(section, {})[line.split("=", 1)[0].strip()] = line
        return out

    wanted = parse(preset)
    lines = text.splitlines()

    for section, keys in wanted.items():
        if section not in [l.strip() for l in lines]:
            lines += [section] + list(keys.values())
            continue
        start = [l.strip() for l in lines].index(section) + 1
        end = next((i for i in range(start, len(lines)) if lines[i].strip().startswith("[")), len(lines))
        while end > start and not lines[end - 1].strip():  # new keys go above the section's trailing blank lines
            end -= 1
        for key, new in keys.items():
            hit = next((i for i in range(start, end) if lines[i].split("=", 1)[0].strip() == key), None)
            if hit is None:
                lines.insert(end, new)
                end += 1
            else:
                lines[hit] = new

    return "\r\n".join(lines) + "\r\n"


def settings(dev_ini, repo_ini, out_ini):
    text = Path(dev_ini).read_text(encoding="utf-8-sig") if os.path.exists(dev_ini) else ""
    preset = Path(repo_ini).read_text(encoding="utf-8-sig")
    with open(out_ini, "w", newline="") as f:
        f.write(render_settings(text, preset))
    print("Settings_v0.ini: graphics updated; other settings kept")


if __name__ == "__main__":
    if len(sys.argv) == 8 and sys.argv[1] == "merge":
        merge(*sys.argv[2:])
    elif len(sys.argv) == 6 and sys.argv[1] == "stock-ntdll":
        stock_ntdll(*sys.argv[2:])
    elif len(sys.argv) == 5 and sys.argv[1] == "env":
        merge_env(*sys.argv[2:])
    elif len(sys.argv) == 5 and sys.argv[1] == "settings":
        settings(*sys.argv[2:])
    else:
        sys.exit(__doc__)
