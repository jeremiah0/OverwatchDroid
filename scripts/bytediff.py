#!/usr/bin/env python3
"""Byte-level diff of two equal-size binaries, or apply such a diff.

  bytediff.py diff  ORIGINAL PATCHED > out.bytediff
  bytediff.py apply ORIGINAL in.bytediff OUTPUT   (refuses if original bytes don't match)
"""
import sys


def diff(orig_path, patched_path):
    a = open(orig_path, "rb").read()
    b = open(patched_path, "rb").read()
    if len(a) != len(b):
        sys.exit(f"size mismatch: {len(a)} vs {len(b)}")
    print(f"# size {len(a)}")
    print("# offset original patched")
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            print(f"0x{i:08x} {x:02x} {y:02x}")


def apply(orig_path, diff_path, out_path):
    data = bytearray(open(orig_path, "rb").read())
    for line in open(diff_path):
        if line.startswith("#") or not line.strip():
            if line.startswith("# size ") and int(line.split()[2]) != len(data):
                sys.exit("original size does not match diff")
            continue
        off, old, new = line.split()
        off, old, new = int(off, 16), int(old, 16), int(new, 16)
        if data[off] != old:
            sys.exit(f"byte mismatch at 0x{off:08x}: expected {old:02x}, found {data[off]:02x}")
        data[off] = new
    open(out_path, "wb").write(data)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "diff":
        diff(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 5 and sys.argv[1] == "apply":
        apply(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.exit(__doc__)
