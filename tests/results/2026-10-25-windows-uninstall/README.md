# Uninstalled Windows programs disappear completely (2026-10-25, dev VM)

Item 18 of the product owner's 2026-10-23 list. 7-Zip 26.04
(`7z2604-x64.exe`, SHA-256 checked) installed through `veltos-run` and
uninstalled from Settings > Apps > Windows programs > ... > Uninstall.

| Picture | What it shows |
|---|---|
| `before-settings.png` | Before the fix: 7-Zip had been uninstalled, but Settings still listed it (VeltOS' installation record) |
| `before-search.png` | Before: Start search still found "7-Zip Help" and "7-Zip File Manager" (Wine's menu entries) |
| `after-settings.png` | The new packages installed, Settings' Windows programs page opened: the old leftovers are gone, the list is empty |
| `after-search.png` | Start search for "zip" finds only VeltOS Archive |
| `reinstalled-listed.png` | 7-Zip installed again: listed with its icon, size and Open / Uninstall |
| `uninstalled-settings.png` | Uninstall chosen and 7-Zip's own uninstaller closed: the row is gone at once |
| `uninstalled-search.png` | ... and Start search no longer finds it |

What Wine's uninstaller had left (checked with `find` in the VM before the
fix): `~/.local/share/applications/wine/Programs/7-Zip/*.desktop` (2),
`~/.config/menus/applications-merged/wine-Programs-7-Zip-*.menu` (2),
`~/.local/share/desktop-directories/wine-Programs*.directory`,
`~/.local/share/icons/hicolor/*/apps/{1DA0_7-zip.0,EA23_7zFM.0}.png` and
VeltOS' record `~/.local/share/veltos/windows/records/7-zip.json`. After
the fix the same `find` printed nothing and the record folder was empty.
While 7-Zip was installed again, its entries stayed (the clean-up runs
after every installation too and only removes entries whose shortcut is
gone).
