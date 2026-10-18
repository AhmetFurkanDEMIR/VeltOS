# veltos-base

Makes the system identify itself as VeltOS.

## What it installs

- `/usr/lib/os-release` (and therefore `/etc/os-release`, a symlink):
  `NAME="VeltOS"`, `ID=veltos`, `ID_LIKE=debian`, `VERSION_ID`, `LOGO=veltos-logo`.

## How

Debian's `base-files` owns `/usr/lib/os-release`. Instead of overwriting it,
`preinst` registers a dpkg diversion that renames Debian's file to
`/usr/lib/os-release.debian`; `base-files` upgrades keep updating that
diverted copy. Removing `veltos-base` removes the diversion and restores
Debian's file (`postrm`).

## Design notes

- `VERSION_CODENAME=trixie` is kept on purpose: third-party repositories and
  install scripts (Steam, NVIDIA, WineHQ, Docker…) derive their APT suite
  from it. `ID_LIKE=debian` lets tools treat VeltOS as Debian.
- `/etc/debian_version` is untouched, for the same compatibility reason.
- `/etc/issue` (TTY login banner) still says Debian — not branded yet.

## Tests

`tests/test_os_release.py` (run during the package build) checks the
identity fields, key syntax and that `VERSION_ID` matches
`debian/changelog`. The ISO build hook `9000-veltos-verify` additionally
checks that the diversion is active inside the image.
