# veltos-msi-ec — MSI laptops' keyboard light (msi-ec, DKMS)

Debian 13's kernel (6.12.113) builds the kernel's own `msi-ec`, but that
version sets only an MSI laptop's battery charge limits: its tables know
where the keyboard light is, yet it registers no LED, so VeltOS Keyboard
Lighting found nothing on an MSI Katana (product owner, 2026-10-28). The
driver's own project, [BeardOverflow/msi-ec](https://github.com/BeardOverflow/msi-ec)
(GPL-2.0-or-later), registers `msiacpi::kbd_backlight` (brightness 0-3)
for the EC firmware versions it knows. This package carries that source
at a pinned commit (`upstream.json`: d7fbbd8 of 2026-08-09, fetched and
checksum-verified at build time) and builds it on the PC with DKMS when
Keyboard Lighting asks for it.

| Path | What |
|---|---|
| `/usr/share/veltos-msi-ec/src/` | msi-ec's source with VeltOS' `dkms.conf` (`data/dkms.conf.in`) |
| `/usr/share/veltos-msi-ec/support.json` | firmware version → `{"keyboard": bool, "models": "..."}`, read from msi-ec.c at build time (`tools/support-table.py`; 373 versions, 208 with a keyboard light at d7fbbd8) |
| `/usr/libexec/veltos/msi-ec-firmware` | prints MSI or not, the model, the EC firmware version (12 bytes at 0xa0 of `/sys/kernel/debug/ec/ec0/io`, built into Debian's kernel read-only) and what msi-ec offers for it, as JSON; pkexec without a password (polkit `org.veltos.msi-ec.firmware`: it only reads) |
| `/usr/libexec/veltos/msi-ec-driver install\|remove\|upgrade` | copies the source to `/usr/src/msi-ec-VERSION`, `dkms add` / `dkms install -k RUNNING_KERNEL`, writes `/etc/modules-load.d/veltos-msi-ec.conf` (msi-ec has no DMI table and does not load by itself), unloads the kernel's own msi_ec and loads the new one; JSON result with a reason (`key`: Secure Boot refused the module, `unsupported`, `nolight`, `build`, ...). pkexec with the administrator's password (`org.veltos.msi-ec.driver`) |
| `veltos_msi_ec/driver.py` | the steps above |

DKMS and the kernel headers are not dependencies: Keyboard Lighting
installs them from Debian (PackageKit) only on MSI laptops that need them,
43 packages / 73.1 MB on a new installation (measured 2026-10-28). With
Secure Boot, Debian's DKMS signs the module with `/var/lib/dkms/mok.key`;
Keyboard Lighting registers that key (mokutil) and the firmware asks for
the one-time password at the next start. Removing the package removes the
DKMS module (prerm); an update to a newer pin rebuilds it where it was
installed (postinst).

Which Katana models get a keyboard light (from `support.json`): Katana
GF66 11U/12U, Katana GF76 11U/12U, Katana 15 B12V/B13VGK, Katana 17 B11UCX,
Katana A17 AI. Not: Katana 15 HX B14W, Katana 17 B12/B13V and 17 HX,
Katana A15 AI (their RGB keyboards have a controller of their own, which
msi-ec does not drive).

## Tests

`tests/test_driver.py`: the firmware version from a made-up EC file, the
support table from the pinned source (package builds), the DKMS and
modprobe steps with stand-ins (Secure Boot refusal, unsupported firmware,
no DKMS), remove and upgrade. The package build also compiles msi-ec
against Debian 13's kernel headers (`override_dh_auto_test`). Not tried
on a real MSI laptop.
