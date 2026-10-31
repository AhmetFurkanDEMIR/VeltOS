#!/usr/bin/env python3
"""Build check: an Xcursor file has images at every given nominal size,
each drawn at 4/3 of it (upstream's 32-unit drawings).

    xcursor_sizes.py FILE SIZE...
"""

import struct
import sys

IMAGE = 0xFFFD0002


def image_sizes(path):
    """{nominal size: (width, height)} of the file's images."""
    with open(path, "rb") as fh:
        data = fh.read()
    magic, _header, _version, count = struct.unpack_from("<4sIII", data, 0)
    if magic != b"Xcur":
        raise ValueError(f"{path}: not an Xcursor file")
    sizes = {}
    for index in range(count):
        kind, nominal, position = struct.unpack_from("<III", data, 16 + 12 * index)
        if kind == IMAGE:
            width, height = struct.unpack_from("<II", data, position + 16)
            sizes[nominal] = (width, height)
    return sizes


def main(argv):
    path, wanted = argv[1], [int(v) for v in argv[2:]]
    sizes = image_sizes(path)
    for size in wanted:
        if sizes.get(size) != (size * 4 // 3, size * 4 // 3):
            print(f"{path}: size {size} missing or wrong: {sizes}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
