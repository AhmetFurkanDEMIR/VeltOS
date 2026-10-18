# veltos-wine-addons

Wine Mono (for .NET Framework programs) and Wine Gecko (for web content
inside Windows programs), in the exact versions Wine 10.0 expects:

| File | Installed to |
|---|---|
| `wine-mono-9.4.0-x86.msi` | `/usr/share/wine/mono/` |
| `wine-gecko-2.47.4-x86.msi`, `wine-gecko-2.47.4-x86_64.msi` | `/usr/share/wine/gecko/` |

## Why

Debian's Wine disables Wine's own downloader for these components and
Debian no longer packages them, so without this package new Wine
environments would lack .NET and HTML support and many programs would fail.
Wine looks for the installers in `/usr/share/wine/` when it creates an
environment and installs them without any network access.

## Verification

`upstream.json` lists the official WineHQ download URLs and the SHA-256
sums that Wine 10.0 itself hard-codes in `dlls/appwiz.cpl/addons.c`.
`build/scripts/fetch-upstream.py` rejects any file that does not match.
When Debian updates Wine to a version that expects other add-on versions,
update `upstream.json` (and the `wine` version range in `debian/control`).
