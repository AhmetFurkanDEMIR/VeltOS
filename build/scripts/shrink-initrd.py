#!/usr/bin/env python3
"""Packs the live initrd's main part with xz instead of zstd.

Debian's initramfs-tools writes the live system's initrd as uncompressed
cpio parts (CPU microcode, the already compressed kernel modules) followed
by the main part compressed with zstd. On the ISO that main part is
84 MB, mostly graphics firmware; xz -9e makes it 17 MB smaller
(measured on ISO 20261026-212523: 84.2 -> 66.8 MB) at about 1 s more
unpacking when the live system starts. It is part of what brings the ISO
under the 2 GiB a GitHub release file may have, with nothing left out.
The installed system makes its own initramfs and keeps zstd (it starts
faster that way).

The kernel unpacks xz initramfs parts with CRC32 checks only
(--check=crc32, as initramfs-tools' own COMPRESS=xz uses); every packed
part is unpacked again and compared before the file is replaced.

Usage: shrink-initrd.py INITRD... (needs zstd and xz)
"""

import subprocess
import sys

ZSTD = b"\x28\xb5\x2f\xfd"
XZ = b"\xfd7zXZ\x00"


def split(data):
    """(uncompressed cpio prefix, compressed rest) of an initramfs image."""
    pos = 0
    while pos < len(data):
        while pos < len(data) and data[pos] == 0:
            pos += 1
        if data[pos:pos + 6] != b"070701":
            return data[:pos], data[pos:]
        while True:                                    # one newc archive
            name_size = int(data[pos + 94:pos + 102], 16)
            file_size = int(data[pos + 54:pos + 62], 16)
            name = data[pos + 110:pos + 110 + name_size - 1]
            pos = (pos + 110 + name_size + 3) & ~3
            pos = (pos + file_size + 3) & ~3
            if name == b"TRAILER!!!":
                break
    return data, b""


def shrink(path):
    data = open(path, "rb").read()
    prefix, rest = split(data)
    if rest.startswith(XZ):
        print(f"veltos-shrink-initrd: {path} is already xz")
        return 0
    if not rest.startswith(ZSTD):
        print(f"veltos-shrink-initrd: {path}: main part is not zstd ({rest[:4].hex()})", file=sys.stderr)
        return 1
    raw = subprocess.run(["zstd", "-q", "-dc"], input=rest, capture_output=True, check=True).stdout
    packed = subprocess.run(["xz", "--check=crc32", "-9e", "-T1", "-c"], input=raw, capture_output=True,
                            check=True).stdout
    again = subprocess.run(["xz", "-dc"], input=packed, capture_output=True, check=True).stdout
    if again != raw:
        print(f"veltos-shrink-initrd: {path}: xz round trip differs", file=sys.stderr)
        return 1
    with open(path, "wb") as out:
        out.write(prefix + packed)
    print(f"veltos-shrink-initrd: {path}: main part {len(rest) / 1e6:.1f} MB zstd -> {len(packed) / 1e6:.1f} MB xz "
          f"(file {len(data) / 1e6:.1f} -> {(len(prefix) + len(packed)) / 1e6:.1f} MB)")
    return 0


def main(argv):
    if not argv:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    return max(shrink(path) for path in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
