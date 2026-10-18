# packages/

VeltOS-specific software, one Debian source package per directory. Each is
built by `build/run.sh packages` (or as part of `build/run.sh iso`) and
installed into the image from a local repository.

| Package | Purpose | Status |
|---|---|---|
| [veltos-base](veltos-base/) | System identity: `os-release` says VeltOS (`ID=veltos`, `ID_LIKE=debian`) via a dpkg diversion | Implemented, unit-tested, verified in VM |
| [veltos-desktop](veltos-desktop/) | Desktop experience: VeltOS Light/Dark themes, Windows 11 style taskbar and **VeltOS Start** menu, colour schemes, generated "Velt Bloom" wallpaper, logo, splash, login/lock screen | Implemented, unit-tested, Start menu verified in VM |
| [veltos-fluent-icons](veltos-fluent-icons/) | Fluent icon + cursor themes (pinned upstream release, Microsoft logos replaced) | Implemented, build-time checks |
| [veltos-boot](veltos-boot/) | Plymouth boot splash, GRUB theme and boot defaults | Implemented, unit-tested; first boot test pending |
| [calamares-settings-veltos](calamares-settings-veltos/) | VeltOS installer: branding, slideshow, Secure Boot capable bootloader setup, offline install | Implemented, unit-tested; **install not yet tested** |

Planned (see `docs/status.md`): Windows application support (`.exe`
double-click), hardware/driver manager, gaming integration, VeltOS
welcome app.

## Adding a package

1. `packages/<name>/debian/` with `control`, `changelog`, `rules`,
   `copyright`, `source/format` (`3.0 (native)`), debhelper compat 13.
2. Tests in `packages/<name>/tests/` (Python `unittest`), run from
   `override_dh_auto_test`. Checks on the *installed* tree go in
   `execute_after_dh_auto_install` (dh_auto_test runs before installation).
3. Third-party sources: pin them in `upstream.json` (URL + SHA-256);
   `build/scripts/fetch-upstream.py` verifies and unpacks them.
4. If the package needs the logo, keep a copy in `branding/`; the repo test
   `tests/repo/test_consistency.py` checks it matches the master.
5. Add the package to a list in `build/live-build/config/package-lists/`
   and, if essential, to `9000-veltos-verify.hook.chroot`.
6. Add a `README.md` explaining what it installs and why.
