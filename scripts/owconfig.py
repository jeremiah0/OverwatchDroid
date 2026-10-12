#!/usr/bin/env python3
"""Edit DroidDeck config for Overwatch without touching other games.

  owconfig.py merge DEVICE_TSV REPO_TSV DEVICE_ENV REPO_ENV OUT_DIR "STORE_DIR ..."
      Replace the device's Overwatch ntdll/fex rows with the repo's, and the
      device's Overwatch entry in game-environment.json with the repo's.
  owconfig.py stock-ntdll DEVICE_TSV OUT_TSV STOCK_HASH STOCK_SOURCE
      Point the Overwatch ntdll row at Valve's original ntdll.dll.

desired.tsv columns: appid, proton name, proton version, component, path, sha256, source.
"""
import json
import os
import sys

APPID = "2357570"
COMPONENTS = {"ntdll", "fex"}


def read_lines(path):
    if not os.path.exists(path):
        return []
    lines = open(path).read().splitlines()
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

    try:
        env = json.load(open(dev_env))
    except (OSError, ValueError):
        env = {}
    env.setdefault("version", 1)
    env.setdefault("shared", {})
    env.setdefault("games", {})[APPID] = json.load(open(repo_env))["games"][APPID]
    with open(os.path.join(out_dir, "game-environment.json"), "w") as f:
        json.dump(env, f, separators=(",", ":"))

    print(f"desired.tsv: kept {len(kept)} rows, set {len(ours)} Overwatch ntdll/fex rows")


def stock_ntdll(dev_tsv, out_tsv, stock_hash, stock_source):
    out, changed = [], 0
    for l in read_lines(dev_tsv):
        fields = l.split("\t")
        if len(fields) >= 7 and fields[0] == APPID and fields[3] == "ntdll":
            fields[5], fields[6] = stock_hash, stock_source
            changed += 1
        out.append("\t".join(fields))
    if not changed:
        sys.exit("no Overwatch ntdll row found; nothing to uninstall")
    with open(out_tsv, "w") as f:
        f.write("\n".join(out) + "\n")
    print(f"pointed {changed} Overwatch ntdll row(s) at the stock ntdll.dll")


if __name__ == "__main__":
    if len(sys.argv) == 8 and sys.argv[1] == "merge":
        merge(*sys.argv[2:])
    elif len(sys.argv) == 6 and sys.argv[1] == "stock-ntdll":
        stock_ntdll(*sys.argv[2:])
    else:
        sys.exit(__doc__)
