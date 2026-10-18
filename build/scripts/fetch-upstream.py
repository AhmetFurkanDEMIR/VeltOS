#!/usr/bin/env python3
"""Fetch and verify the pinned upstream sources of a VeltOS package.

    fetch-upstream.py PACKAGE_DIR DEST_DIR [--cache DIR]

PACKAGE_DIR/upstream.json pins either one release tarball, unpacked into
DEST_DIR without its top-level directory:

    {"name": "...", "version": "...", "url": "https://...", "sha256": "..."}

or a list of plain files, copied into DEST_DIR as they are:

    {"name": "...", "version": "...",
     "files": [{"name": "x.msi", "url": "https://...", "sha256": "..."}]}

Every download must match its pinned SHA-256; anything else is rejected, so
packages never contain unverified downloads. Downloads are cached.
"""

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url, expected_sha256, cache_name, cache_dir):
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / cache_name
    if target.exists() and sha256(target) == expected_sha256:
        return target
    print(f"downloading {url}", file=sys.stderr)
    with tempfile.NamedTemporaryFile(dir=cache_dir, delete=False) as tmp:
        with urllib.request.urlopen(url, timeout=300) as resp:
            shutil.copyfileobj(resp, tmp)
    actual = sha256(tmp.name)
    if actual != expected_sha256:
        Path(tmp.name).unlink()
        raise SystemExit(f"checksum mismatch for {url}: expected {expected_sha256}, got {actual}")
    Path(tmp.name).replace(target)
    return target


def unpack(tarball, dest):
    with tarfile.open(tarball) as tar:
        members = []
        for member in tar.getmembers():
            parts = Path(member.name).parts
            if len(parts) < 2:
                continue
            member.name = str(Path(*parts[1:]))
            members.append(member)
        tar.extractall(dest, members=members, filter="data")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("dest", type=Path)
    parser.add_argument("--cache", type=Path, default=Path("/out/cache/upstream"))
    args = parser.parse_args()

    pin = json.loads((args.package_dir / "upstream.json").read_text())
    for key in ("name", "version"):
        if not pin.get(key):
            raise SystemExit(f"upstream.json: missing {key}")
    if args.dest.exists():
        shutil.rmtree(args.dest)
    args.dest.mkdir(parents=True)

    if "files" in pin:
        for item in pin["files"]:
            for key in ("name", "url", "sha256"):
                if not item.get(key):
                    raise SystemExit(f"upstream.json: file entry missing {key}")
            cached = fetch(item["url"], item["sha256"], item["name"], args.cache)
            shutil.copy(cached, args.dest / item["name"])
    else:
        for key in ("url", "sha256"):
            if not pin.get(key):
                raise SystemExit(f"upstream.json: missing {key}")
        tarball = fetch(pin["url"], pin["sha256"], f"{pin['name']}-{pin['version']}.tar.gz", args.cache)
        unpack(tarball, args.dest)
    print(f"{pin['name']} {pin['version']}: all downloads verified (sha256), unpacked to {args.dest}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
