# packages/

VeltOS-specific software, one Debian source package per directory. Each is
built by `build/run.sh packages` (or as part of `build/run.sh iso`) and
installed into the image from a local repository.

| Package | Purpose | Status |
|---|---|---|
| [veltos-base](veltos-base/) | System identity: `/usr/lib/os-release` says VeltOS (`ID=veltos`, `ID_LIKE=debian`) via a dpkg diversion | Implemented, unit-tested |
| [veltos-desktop](veltos-desktop/) | Plasma desktop experience: VeltOS Dark/Light global themes, centered taskbar, colour schemes, wallpaper, splash, login/lock screen branding, logo | Implemented, unit-tested |

Planned (see `docs/status.md`): hardware manager (Milestone 2), Windows
application manager (Milestone 3), gaming integration (Milestone 4),
VeltOS Calamares settings (Milestone 5).

## Adding a package

1. `packages/<name>/debian/` with `control`, `changelog`, `rules`,
   `copyright`, `source/format` (`3.0 (native)`), debhelper compat 13.
2. Tests in `packages/<name>/tests/` (Python `unittest`), run from
   `override_dh_auto_test` in `debian/rules`.
3. Add the package name to a list in
   `build/live-build/config/package-lists/` and, if it is essential, to
   the checks in `9000-veltos-verify.hook.chroot`.
4. Add a `README.md` explaining what it installs and why.
