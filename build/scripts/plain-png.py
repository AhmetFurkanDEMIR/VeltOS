#!/usr/bin/env python3
"""Rewrite PNG files so that GRUB can always read them.

    plain-png.py FILE.png...

GRUB's PNG reader failed on the live boot menu background of one build
(ISO 20261020-083729: the menu stayed black and GRUB waited; the same
picture with a different build date worked). The picture is rewritten
with every row unfiltered (filter type 0) and the image data stored
uncompressed (deflate "stored" blocks), the simplest form a PNG decoder
can read; the pixels do not change. 8-bit RGB and RGBA without
interlacing only (what rsvg-convert writes); anything else is an error.
"""

import struct
import sys
import zlib
from pathlib import Path

SIGNATURE = b"\x89PNG\r\n\x1a\n"


def chunks(data):
    if not data.startswith(SIGNATURE):
        raise ValueError("not a PNG file")
    pos = len(SIGNATURE)
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        yield kind, data[pos + 8:pos + 8 + length]
        pos += 12 + length


def chunk(kind, body):
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def unfilter(raw, width, height, bpp):
    stride = width * bpp
    rows, prev, pos = [], bytearray(stride), 0
    for _ in range(height):
        kind = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if kind == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif kind == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif kind == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif kind == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upper_left = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + paeth(left, prev[i], upper_left)) & 0xFF
        elif kind != 0:
            raise ValueError(f"unknown PNG filter {kind}")
        rows.append(bytes(line))
        prev = line
    return rows


def plain(data):
    header, idat, others = None, b"", []
    for kind, body in chunks(data):
        if kind == b"IHDR":
            header = body
        elif kind == b"IDAT":
            idat += body
        elif kind != b"IEND":
            others.append((kind, body))
    width, height, depth, colour, _compression, _filter, interlace = struct.unpack(">IIBBBBB", header)
    if depth != 8 or colour not in (2, 6) or interlace:
        raise ValueError("only 8-bit RGB/RGBA PNG files without interlacing are supported")
    bpp = 3 if colour == 2 else 4
    rows = unfilter(zlib.decompress(idat), width, height, bpp)
    raw = b"".join(b"\x00" + row for row in rows)
    out = SIGNATURE + chunk(b"IHDR", header)
    out += b"".join(chunk(kind, body) for kind, body in others)
    out += chunk(b"IDAT", zlib.compress(raw, 0)) + chunk(b"IEND", b"")
    return out


def main(argv):
    for name in argv[1:]:
        path = Path(name)
        path.write_bytes(plain(path.read_bytes()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
