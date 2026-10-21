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
- **App icons as one family** (`branding/apps/`, drawn by
  `tools/app-icons.py`): Calculator, Camera, Mail, Snipping Tool, Store,
  Settings, Task Manager, File Explorer, Notepad, Photos, Document Viewer,
  Archive, Media Player and Disk Management in the look of Windows 11's
  app icons (VeltOS drawings, no Microsoft files or logos), installed under
  the VeltOS apps' names and the KDE/Debian apps they stand for. The
  Office apps (Word Processor, Spreadsheet, Presentation, for LibreOffice)
  follow the composition of Microsoft 365's Windows 11 icons: a tile in
  the app's colour (Word blue, Excel green, PowerPoint orange) with the
  app's initial (W, S, P: VeltOS' own app names) in front of a page, sheet
  or slide; the same drawings stand for the Office file types.
- **Firefox** shows its own logo (the firefox-esr package's hicolor
  icons), as on Windows 11: Fluent's flat redrawings of it are removed.
- **Special folders** coloured like Windows 11's (Desktop, Downloads,
  Documents, Pictures, Music, Videos) with 16 px drawings, and File
  Explorer's orange Home (`veltos-home`).
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
