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
- **Drives** (`tools/draw-icons.py`, 2026-10-24): the local disk, the
  Windows drive (the disk with a blue framed window on its front; not
  Microsoft's four-pane logo, a trademark) and a USB stick in the same
  family (light grey, a metal plug, a blue light) replace Fluent's
  `drive-harddisk`, `drive-removable-media`, `drive-removable-media-usb`
  and `-pendrive` (a dark stick with an eject badge), with their own
  16 px drawings; the large ones fill the frame as Windows 11's do.
- **App icons as one family** (`branding/apps/`, drawn by
  `tools/app-icons.py`): Calculator, Camera, Mail, Calendar, Snipping
  Tool, Store, Settings, Task Manager, File Explorer, Notepad, Photos,
  Document Viewer, Archive, Media Player and Disk Management in the look
  of Windows 11's app icons (VeltOS drawings, no Microsoft files or
  logos), installed under the VeltOS apps' names and the KDE/Debian apps
  they stand for (Calendar also as `office-calendar`,
  `x-office-calendar`, KOrganizer and GNOME Calendar). Camera is a wide
  body (about 3:2, like Windows 11's) with a large lens: the first, nearly
  square drawing looked squeezed next to the other icons (product owner,
  2026-10-22). The
  Office apps (Word, Excel, PowerPoint: LibreOffice under the names the
  product owner chose on 2026-10-22) follow the composition of Microsoft
  365's Windows 11 icons: a tile in the app's colour (Word blue, Excel
  green, PowerPoint orange) with the initial W, X or P in front of a page,
  sheet or slide; the same drawings stand for the Office file types.
- **Firefox** shows its own logo (the firefox-esr package's hicolor
  icons), as on Windows 11: Fluent's flat redrawings of it are removed.
  Its logo fills the whole square, while the VeltOS icons around it leave
  about an eighth free on each side, so next to them it looked too big
  (product owner, 2026-10-22): `/usr/libexec/veltos/pad-app-icon`
  (`tools/pad-app-icon`) embeds the program's largest hicolor PNG
  unchanged, drawn at 84 % in the middle of an SVG of the same icon name
  in `.Fluent-base/scalable/apps/` (`firefox-esr.svg`, `firefox.svg`),
  which the Fluent themes find before hicolor. The postinst makes these
  files on the target system and again whenever Firefox installs new
  icons (dpkg trigger on `/usr/share/icons/hicolor/128x128/apps`,
  `debian/veltos-fluent-icons.triggers`); the prerm removes them. Files of
  that name the tool did not write are left alone.
- **Special folders** coloured like Windows 11's (Desktop, Downloads,
  Documents, Pictures, Music, Videos) with 16 px drawings, and File
  Explorer's orange Home (`veltos-home`; File Explorer's own windows now
  draw its house in the accent colour, veltos-explorer
  `LocationIcon.qml`).
- **"This PC" and Recycle Bin** (`branding/computer.svg`, `user-trash.svg`,
  `user-trash-full.svg`, drawn by `tools/draw-icons.py`): VeltOS artwork in
  the look of Windows 11's icons (a monitor with a cyan-to-blue screen on a
  grey stand; a frosted glass bin with a grey foot and the blue recycling
  arrows, empty and full of crumpled paper) replaces Fluent's icons of
  these names at all sizes. Microsoft's own icon files are not used.
- **Yellow folders like Windows 11** (`tools/recolour-folders.py`): the
  folder and place icons and the File Explorer icon are solid yellow
  instead of Fluent's translucent blue, and Fluent's monochrome 16-24 px
  place icons are dropped so the coloured ones also appear in small sizes
  (File Explorer's navigation pane), as on Windows 11.
- Dangling upstream symlinks are removed.
- **Fluent cursors are the system default** (`x-cursor-theme` alternative,
  priority 110 over Debian's Adwaita at 90; `Fluent-cursors/cursor.theme`),
  so programs that do not read the desktop's cursor setting (some X11
  programs, programs started as root) show the same pointer.

Checks run during the build (`execute_after_dh_auto_install` in
`debian/rules`): Breeze fallback, no dangling links, key app icons exist,
cursors present, `start-here` is the VeltOS logo, no `wine.svg` left,
folders recoloured.

Tests (`tests/test_pad_app_icon.py`, run by `override_dh_auto_test`):
`pad-app-icon` takes the largest PNG, embeds it unchanged with the
margin, removes its own file when the program's icons are gone and leaves
a file it did not write alone. The tool needs `python3` (Depends).
