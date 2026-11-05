#!/usr/bin/env python3
"""Verify every bundled legacy binary before contacting a device."""
import hashlib
from pathlib import Path
import sys


def verify(repo):
    root = (repo / "store").resolve()
    expected = set()
    for line in (repo / "SHA256SUMS").read_text().splitlines():
        checksum, name = line.split()
        path = (root / name).resolve()
        if root not in path.parents or path in expected:
            raise ValueError("Invalid or duplicate payload path")
        expected.add(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
            raise ValueError(f"Bundled file failed its checksum: {name}")
    # Finder drops .DS_Store into any folder it opens; it never reaches a device.
    actual = {p.resolve() for p in root.rglob("*") if p.is_file() and p.name not in (".complete", ".DS_Store")}
    if actual != expected or not expected:
        raise ValueError("The bundled files and SHA256SUMS do not match")


if __name__ == "__main__":
    try:
        verify(Path(__file__).resolve().parent.parent)
    except (ValueError, OSError) as error:
        sys.exit(f"{error}. Download a fresh copy before trying again.")
