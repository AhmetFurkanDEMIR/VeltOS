# veltos-fluent-icons

Packages the [Fluent icon theme](https://github.com/vinceliuice/Fluent-icon-theme)
by Vince Liuice (GPL-3.0) for VeltOS: clean, colourful icons in the style
of Windows 11, plus the Fluent cursor themes.

## Source pinning

`upstream.json` pins one upstream release (tag `2026-07-27`) and its
SHA-256. `build/scripts/fetch-upstream.py` downloads it, refuses anything
that does not match the checksum, and unpacks it to `upstream/` before
`dpkg-buildpackage` runs. To update: change the URL/version, put the new
checksum in `upstream.json`, rebuild, and look at the result in the VM.

## VeltOS changes to upstream

- Icons that Fluent lacks fall back to **Breeze** (upstream inherits only
  `hicolor`), so KDE applications never show blank icons.
- **No Microsoft logos:** upstream draws `start-here*` as the Windows 11
  logo and the Wine icons as the Windows flag. `start-here*` and
  `distributor-logo*` are replaced by the VeltOS logo (these icons mean
  "this operating system"); the Wine/Windows icons are removed so Breeze's
  neutral icons are used.
- **Yellow folders like Windows 11** (`tools/recolour-folders.py`): the
  folder and place icons and the File Explorer icon are solid yellow
  instead of Fluent's translucent blue, and Fluent's monochrome 16-24 px
  place icons are dropped so the coloured ones also appear in small sizes
  (File Explorer's navigation pane), as on Windows 11.
- Dangling upstream symlinks are removed.

Checks run during the build (`execute_after_dh_auto_install` in
`debian/rules`): Breeze fallback, no dangling links, key app icons exist,
cursors present, `start-here` is the VeltOS logo, no `wine.svg` left,
folders recoloured.
