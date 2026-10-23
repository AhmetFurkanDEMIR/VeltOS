# veltos-base

Makes the system identify itself as VeltOS.

## What it installs

- `/usr/lib/os-release` (and therefore `/etc/os-release`, a symlink):
  `NAME="VeltOS"`, `ID=veltos`, `ID_LIKE=debian`, `VERSION_ID`, `LOGO=veltos-logo`,
  `HOME_URL` and `SUPPORT_URL` (the VeltOS website,
  https://veltos.ahmetfurkandemir.com/).
- `/etc/issue`, `/etc/issue.net`: "VeltOS 0.1" console login banners.
- `/etc/motd`, the message after a console sign-in (Automatic Repair's
  Command Prompt, Ctrl+Alt+F2): VeltOS' wording of Debian's licence and
  warranty notice. base-files owns no `/etc/motd` (it copies its text there
  when the file is missing), so `postinst` replaces it only while it is
  still Debian's text, and `postrm` brings Debian's back (2026-10-23).

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
- `/etc/issue` and `/etc/issue.net` (console login banners) say VeltOS:
  base-files' versions are diverted to `*.debian` and `postinst` copies
  the VeltOS ones from `/usr/share/veltos-base/`.

## Tests

`tests/test_os_release.py` (run during the package build) checks the
identity fields, key syntax and that `VERSION_ID` matches
`debian/changelog`. The ISO build hook `9000-veltos-verify` additionally
checks that the diversion is active inside the image.
