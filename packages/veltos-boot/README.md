# veltos-boot

The VeltOS start-up experience.

| Piece | Installed to | Notes |
|---|---|---|
| Plymouth theme `veltos` | `/usr/share/plymouth/themes/veltos/` | Logo in the centre and a spinner of white dots below it on a near-black background, like Windows. Made the default through the `default.plymouth` alternative (priority 200); the initramfs is rebuilt via a dpkg trigger. Password prompt images are shared with Plymouth's `spinner` theme. |
| GRUB theme `veltos` | `/usr/share/grub/themes/veltos/` | For installed systems: logo and "VeltOS" on navy, menu below. |
| Boot defaults | `/etc/default/grub.d/veltos.cfg` | `GRUB_DISTRIBUTOR="VeltOS"` (menu says "VeltOS GNU/Linux"), `quiet splash`, theme, os-prober enabled so Windows is listed. |

All images are generated at package build time by `tools/build-assets.py`
from `branding/veltos-logo.svg` (a copy of the master logo in
`veltos-desktop`; `tests/repo/test_consistency.py` keeps them identical).

The live ISO's own boot menu is configured in
`build/live-build/config/bootloaders/`, not here.

Tests: `tests/test_boot.py` (theme file, spinner animation loops, GRUB
defaults).
