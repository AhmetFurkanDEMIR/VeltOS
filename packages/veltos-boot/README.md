# veltos-boot

The VeltOS start-up experience.

| Piece | Installed to | Notes |
|---|---|---|
| Plymouth theme `veltos` | `/usr/share/plymouth/themes/veltos/` | Logo in the centre and a spinner of white dots below it on a near-black background, like Windows. Password prompt images are shared with Plymouth's `spinner` theme. |
| Plymouth defaults | `/usr/share/plymouth/plymouthd.defaults` (Plymouth's own file diverted to `plymouthd.defaults.debian`) | `Theme=veltos`. This file — not the `default.plymouth` alternative, which is also set — is what `plymouth-set-default-theme` and the initramfs hook read. Before this diversion the theme named there was not installed and every initramfs (also the live ISO's) fell back to the text splash. The initramfs is rebuilt via a dpkg trigger. |
| SDDM ordering | `/usr/lib/systemd/system/sddm.service.d/veltos-plymouth.conf` | `After=plymouth-quit.service`, as upstream SDDM's unit has it; without it automatic login of the live session sometimes failed (`sddm-helper` exit 63). |
| GRUB theme `veltos` | `/usr/share/grub/themes/veltos/` | For installed systems: logo and "VeltOS" on navy, menu below in Inter (converted with `grub-mkfont`), rounded highlight for the selected entry, thin countdown bar. |
| Boot defaults | `/etc/default/grub.d/veltos.cfg` | `GRUB_DISTRIBUTOR="VeltOS"`, `quiet splash`, theme, os-prober enabled so Windows is listed, menu hidden like on Windows (`GRUB_TIMEOUT_STYLE=hidden`, 2 s; Esc/F4/Shift shows it), fixed video mode `1024x768,800x600,auto` (plain `auto` made VirtualBox on Hyper-V stop the VM with a triple fault when Linux started — reproduced and fixed on a copy of the product owner's installed disk). |
| GRUB entries | `/etc/grub.d/10_linux` (copied there by the postinst from `/usr/lib/veltos-boot/grub.d/`; Debian's script diverted to `/etc/grub.d/10_linux.dpkg-veltos`) | Runs Debian's script and renames "VeltOS GNU/Linux" to "VeltOS" and drops the "Loading Linux …" messages. Not shipped as a conffile: a conffile at a diverted conffile's path made dpkg stop with a question during the upgrade test. |
| Menu and text | `/etc/grub.d/35_veltos` | Draws GRUB's own text black on black and shows the menu for 5 s when os-prober finds other systems (dual boot). |

All images and fonts are generated at package build time by
`tools/build-assets.py` from `branding/veltos-logo.svg` (a copy of the
master logo in `veltos-desktop`; `tests/repo/test_consistency.py` keeps
them identical) and Debian's `fonts-inter`.

GRUB font names: `grub-mkfont` names a font "<family> <Regular|Bold> <size>";
Inter's SemiBold file reports family "Inter" and style Regular, so it is
converted with the family name "Inter SemiBold" — themes refer to it as
"Inter SemiBold Regular 20". The build checks every name.

The live ISO's own boot menu is configured in
`build/live-build/config/bootloaders/`; `build/scripts/build-iso.sh` copies
this package's GRUB fonts and highlight images into it.

Tests: `tests/test_boot.py` (theme file, spinner animation loops, Plymouth
defaults, SDDM drop-in, diversion scripts, GRUB theme uses only generated
fonts, highlight slices) and install-tree checks in `debian/rules`.
