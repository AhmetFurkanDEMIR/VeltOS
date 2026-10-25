# veltos-office

VeltOS Office: LibreOffice's word processor (Writer), spreadsheet (Calc)
and presentation program (Impress) from Debian, behind the start screen of
Microsoft 365's apps on Windows 11, set up for people who come from
Microsoft Office. VeltOS does not write its own office suite; it is
LibreOffice underneath (Help > About says so with the version), and this
package adds the start screen, templates and one configuration layer.

## The start screen (`veltos-office word|sheet|slides`)

A PySide6/QML window (`veltos_office/app.py`, `qml/`) in the layout of
Word's / Excel's / PowerPoint's start screen: the title bar and the
navigation rail in the app's colour (Word blue `#185ABD`, Excel green
`#107C41`, PowerPoint orange `#C43E1C`; dark mode: black chrome with the
colour as accent), pages on the right:

- **Home**: "Good morning / afternoon / evening", **New** with the blank
  document tile and the first templates ("More templates →"), then
  **Recent / Pinned** with a search box, "Name" / "Date modified" columns,
  rows grouped by Pinned / Today / Yesterday / This week / Last week /
  Older, a pin on hover, a right-click menu (Open, Pin, Open file
  location, Copy path, Remove from list).
- **New**: every template as a grid with search.
- **Open**: Recent, This PC (Documents, Desktop, Downloads) and Browse,
  which open the VeltOS Open dialog (`veltos-explorer --pick`, filtered
  to the app's file types).
- **Account**: the user's picture and name, "Manage account" (VeltOS
  Settings > Accounts), the theme (follows VeltOS' light/dark mode),
  product information.
- **Options**: the start screen switch (off: a blank document opens at
  once), clearing the recent list, where the other options live.

Animations as on Windows 11: sections glide in one after the other when a
page opens, tiles lift with a shadow on hover, the rail's indicator and
the tabs' underline slide, the Windows 11 toggle; all off when Settings >
Accessibility > Visual effects turns animations off
(`AnimationDurationFactor=0`). Text sizes follow Settings > Accessibility
> Text size.

Where the data comes from:

- Recent files: LibreOffice's own list (`PickList` in the user profile's
  `registrymodifications.xcu`, with the filter each file was opened with;
  `recent.py`), filtered to the app's file types, plus the files the start
  screen opened itself (LibreOffice records them only later). Pins and
  options live in `~/.config/veltos-office/<kind>.json`.
- Templates (`templates.py`): VeltOS' own from
  `/usr/share/veltos-office/templates/<kind>` (built by
  `tools/make-templates.py` at package build time: flat ODF written in
  Python, converted by LibreOffice into `.ott`/`.ots` with thumbnails;
  meeting notes, report, to-do list; monthly budget, invoice, expense
  tracker, weekly schedule), LibreOffice's (`share/template/common`:
  business letters, business card, CV, résumé; the 23 presentation
  designs) and the user's (`~/.config/libreoffice/4/user/template`).
  Thumbnails are the pictures inside the template files, cached in
  `~/.cache/veltos-office/thumbnails`.
- Opening: `libreoffice --nologo --writer` (blank), `-n TEMPLATE` (new
  document from a template) or the file; the start screen shows a
  progress line and leaves 2.5 s later, while LibreOffice brings its
  window up.

The Start entries "Word Processor", "Spreadsheet", "Presentation"
(veltos-desktop `update-app-names`) run `veltos-office word|sheet|slides %U`
when this package is installed: with files, LibreOffice opens them at
once; without, the start screen appears. Their "New Document" actions pass
`--blank`.

## Blank documents for the New menus

File Explorer's and the desktop's New > Word Document / PowerPoint
Presentation / Excel Worksheet make an empty file with Windows' name and
run `/usr/libexec/veltos-office/blank-document PATH` (`blank.py`), which
fills new, empty files by their extension and never touches a file with
content. A `.docx` or `.pptx` stays empty, as on Windows: LibreOffice
opens an empty file as a new document of that type with the user's
defaults and saves it in that format. A `.xlsx` becomes a small workbook
(Calibri 11, first sheet "Sheet1" / "Sayfa1"), as Windows copies a
template for Excel: Calc gave an empty `.xlsx` no app icon in the title
bar and on the taskbar.

## The configuration layer

`registry/veltos-office.xcd`, installed in LibreOffice's `share/registry`
(read with LibreOffice's own defaults; what users change in LibreOffice is
stored on top of it and wins). It names `main`, `writer`, `calc` and
`impress` as dependencies: LibreOffice parses an .xcd after the files it
depends on and later files win, and the document factories live in
writer/calc/impress.xcd, which sort after this file (without the
dependencies the Save dialog still offered .odt):

- the ribbon-like **Tabbed** interface in all three programs;
- the **Colibre** icons (LibreOffice's icon set in Microsoft Office's style);
- new documents are saved as **.docx, .xlsx, .pptx**, without the "Keep
  current format?" question;
- text in new documents, spreadsheets and presentations is Carlito
  (Calibri's metrics), 11 pt in the word processor;
- window titles read **"Untitled 1 — VeltOS Office Writer"** like
  "Document1 - Word" (`ooName`; the module name is LibreOffice's localized
  `ooSetupFactoryUIName`, which an unlocalized empty value does not
  replace); `%PRODUCTNAME` in LibreOffice's dialogs is "VeltOS Office" too;
- LibreOffice's Start Center (shown when the last document is closed) in
  light colours;
- no Tip of the Day, no donation, "get involved" or release-notes bars;
  crash reports to The Document Foundation off.

Debian's own presentation template ("DebianTalk") is diverted out of
LibreOffice's template folders (`dpkg-divert`, preinst/postrm).

Dependencies: `libreoffice-kf6` (Qt 6/Plasma integration, so the VeltOS
Kvantum style applies and file dialogs go through the desktop portal to
the VeltOS dialog), the Colibre icons, and fonts with the metrics of
Calibri/Cambria (Carlito, Caladea) and Arial/Times New Roman/Courier New
(Liberation), so documents from Windows keep their layout.

Elsewhere: the apps are named **Word**, **Excel** and **PowerPoint** in
Start and on the start screens (the product owner's choice, 2026-10-22;
the generic names Word Processor / Spreadsheet / Presentation and their
Turkish forms stay as search words; veltos-desktop `update-app-names`),
and their icons (veltos-fluent-icons) follow the composition of Microsoft
365's Windows 11 icons: a coloured tile with the initial W / X / P in
front of a page, sheet or slide (VeltOS drawings, no Microsoft files).
The windows' title bars take the app's colour from the VeltOS window
frame (veltos-desktop, `plasma-overrides/aurorae.json`, told by the
caption).

## Tests

- `tests/test_office.py`: texts in both languages, the blank workbook
  (parts, well-formed XML, the sheet's name, the same bytes every time)
  and `blank-document` (empty Word/PowerPoint files kept, content never
  replaced), the recent list
  (LibreOffice's PickList, own openings, pins, missing files), templates
  with thumbnails (fake template files), the LibreOffice command lines,
  the template sources' XML, and the window loaded offscreen for each
  app in English and Turkish (every page, pinning, opening; any QML
  warning fails).
- `tests/test_config.py` checks every setting of the layer against the
  schema and data of the LibreOffice it is built with (Build-Depends):
  components, groups, properties, the "Tabbed" mode, the document
  factories, the Word/Excel/PowerPoint filters, the product name, the
  Colibre icons.

## Not done

The document window is LibreOffice's: the Tabbed interface and Colibre
icons come close to Office's ribbon, but its tab strip is not in the app's
colour and it has no animations (that would need changes to LibreOffice
itself; LibreOffice's GTK plug-in with GTK CSS was tried on 2026-10-22 and
coloured only the tabs themselves, see the development log). Closing the last document shows LibreOffice's Start Center, not
the VeltOS start screen. Dark mode icons untested; real Office documents
not yet compared.
