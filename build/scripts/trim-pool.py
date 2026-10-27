#!/usr/bin/env python3
"""Leaves out of the ISO's package pool what the installed system already has.

The pool (binary/pool, from config/package-lists/*.list.binary) lets the
installer set up the bootloader without a network connection
(calamares-settings-veltos: sources-media, bootloader-config). live-build
puts every dependency of the listed packages into it, also those already
installed in the live system at the same version (libc6, systemd,
coreutils, perl-base ...): about 40 MB of the ISO that apt never takes,
because the installed system is a copy of the live system.

A package stays in the pool when the live system does not have it at that
version, or when the installer removes it before installing the bootloader:
Calamares' package job purges the live packages with autoremove
(modules/packages.conf), so whatever that removal would take with it is
simulated with apt in the live chroot and kept.

Run in live-build's binary/ directory (a binary hook): ../chroot is the live
system. Regenerates dists/<suite>/main/binary-<arch>/Packages(.gz) and the
checksums in dists/<suite>/Release. Standard library, dpkg-deb, apt-ftparchive
and chroot.
"""

import gzip
import hashlib
import re
import subprocess
import sys
from pathlib import Path

CHROOT = Path("../chroot")
PACKAGES_CONF = CHROOT / "etc/calamares/modules/packages.conf"


def installed(status_text):
    """{(package, architecture, version)} of the packages dpkg has installed."""
    found = set()
    for stanza in status_text.split("\n\n"):
        fields = {}
        for line in stanza.splitlines():
            match = re.match(r"^([A-Za-z-]+): (.*)$", line)
            if match:
                fields[match.group(1)] = match.group(2)
        if fields.get("Status", "").endswith(" installed"):
            found.add((fields.get("Package"), fields.get("Architecture"), fields.get("Version")))
    return found


def installer_removals(conf_text):
    """The package names the installer's package job removes."""
    names = []
    in_remove = False
    for line in conf_text.splitlines():
        if re.match(r"^\s*-\s*remove:\s*$", line):
            in_remove = True
            continue
        match = re.match(r"^\s*-\s*'?([a-z0-9][a-z0-9+.-]*)'?\s*$", line)
        if in_remove and match:
            names.append(match.group(1))
        elif in_remove and line.strip() and not line.strip().startswith("#"):
            in_remove = False
    return names


def removed_with_autoremove(simulation):
    """Package names in `apt-get -s purge --autoremove` output."""
    return {re.split(r"[: ]", line.split()[1])[0]
            for line in simulation.splitlines() if line.startswith(("Purg ", "Remv "))}


def deb_fields(deb):
    out = subprocess.run(["dpkg-deb", "-f", str(deb), "Package", "Version", "Architecture"],
                         capture_output=True, text=True, check=True).stdout
    fields = dict(line.split(": ", 1) for line in out.splitlines() if ": " in line)
    return fields["Package"], fields["Architecture"], fields["Version"]


def checksum_sections(suite_dir):
    files = sorted(p for p in suite_dir.rglob("*") if p.is_file() and p != suite_dir / "Release")
    sections = []
    for title, algorithm in (("MD5Sum", "md5"), ("SHA1", "sha1"), ("SHA256", "sha256"), ("SHA512", "sha512")):
        sections.append(f"{title}:")
        for path in files:
            data = path.read_bytes()
            digest = hashlib.new(algorithm, data).hexdigest()
            sections.append(f" {digest} {len(data):>16} {path.relative_to(suite_dir).as_posix()}")
    return "\n".join(sections) + "\n"


def main():
    pool = Path("pool")
    if not pool.is_dir():
        print("veltos-trim-pool: no package pool, nothing to do")
        return 0
    have = installed((CHROOT / "var/lib/dpkg/status").read_text(encoding="utf-8", errors="replace"))
    have_names = {name for name, _arch, _version in have}
    removals = [n for n in installer_removals(PACKAGES_CONF.read_text(encoding="utf-8")) if n in have_names]
    simulation = subprocess.run(["chroot", str(CHROOT), "apt-get", "-s", "-o", "Debug::NoLocking=1",
                                 "purge", "--autoremove", *removals],
                                capture_output=True, text=True)
    if simulation.returncode != 0:
        print(simulation.stdout + simulation.stderr, file=sys.stderr)
        print("veltos-trim-pool: apt could not simulate the installer's removals", file=sys.stderr)
        return 1
    removed = removed_with_autoremove(simulation.stdout)
    kept, dropped, saved = 0, 0, 0
    for deb in sorted(pool.rglob("*.deb")):
        name, arch, version = deb_fields(deb)
        if (name, arch, version) in have and name not in removed:
            saved += deb.stat().st_size
            deb.unlink()
            dropped += 1
        else:
            kept += 1
    for folder in sorted((p for p in pool.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        if not any(folder.iterdir()):
            folder.rmdir()
    for suite_dir in Path("dists").iterdir():
        for index in suite_dir.glob("main/binary-*/Packages"):
            text = subprocess.run(["apt-ftparchive", "packages", "pool"], capture_output=True, text=True,
                                  check=True).stdout
            index.write_text(text, encoding="utf-8")
            with gzip.GzipFile(index.with_suffix(".gz"), "wb", compresslevel=9, mtime=0) as packed:
                packed.write(text.encode("utf-8"))
        release = suite_dir / "Release"
        header = release.read_text(encoding="utf-8").split("\nMD5Sum:", 1)[0].rstrip("\n") + "\n"
        release.write_text(header + checksum_sections(suite_dir), encoding="utf-8")
    print(f"veltos-trim-pool: kept {kept} packages, left out {dropped} the installed system already has "
          f"({saved / 1e6:.1f} MB); the installer's removals keep {len(removed)} packages in the pool")
    return 0


if __name__ == "__main__":
    sys.exit(main())
