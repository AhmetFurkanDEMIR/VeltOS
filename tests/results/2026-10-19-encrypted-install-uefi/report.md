# Encrypted installation test — 2026-10-19, QEMU/KVM, UEFI

Manual test (driven with `build/run.sh vm`), 6 GiB RAM, new 40 GiB disk.

ISO: `veltos-0.1.0-dev-20261019-170820` (installation). The unlock screen
changes (font, texts, layout) and `tries=0` were then applied to the
installed system from the newer `veltos-boot` and installer packages
(`dpkg -i`, installer job run by hand) and checked by rebooting; the ISO
built afterwards contains them (see `docs/dev/development-log.md`).

## Steps and observations

1. Live session -> Install -> "Erase disk" + "Encrypt system", password
   `veltos123`, user "Test User". Calamares finished ("All done"); the
   session log shows the `hwclock` job ("Hwclock set using RTC method")
   and the `efi-label` job.
2. Firmware boot entry: `Boot0009* VeltOS ... File(\EFI\debian\shimx64.efi)`.
   `/boot/grub/grub.cfg`: entries "VeltOS", "VeltOS, with Linux 6.12.113",
   "... (recovery mode)" (the GRUB entries bug of the previous test is
   fixed).
3. Boot from disk: the VeltOS boot screen asks for the password
   (`01-unlock-prompt.png`, after the changes; before them the prompt read
   "Please unlock disk luks-<uuid>" in a monospace font over the logo).
4. Four wrong passwords in a row (`tries=0`): the screen kept asking, no
   recovery shell. (That run used a first version of the texts, which
   showed the warning as a separate message; it stayed visible while the
   correct password was being checked, so the final version shows it in
   the prompt.) Final version: one wrong password -> "The password is
   incorrect. Try again." under the box (`02-wrong-password.png`).
5. Correct password: spinner without leftover messages
   (`03-unlocking.png`), then the VeltOS sign-in screen; signing in
   reaches the desktop with the taskbar.

## Repeated on the ISO with all changes

ISO `veltos-0.1.0-dev-20261019-174700`, new disk, same choices. Calamares
ran the `crypttab-tries` job ("All done"); the installed system has
`luks-<uuid> UUID=<uuid> none tries=0` in `/etc/crypttab`, the firmware
entry `Boot0009* VeltOS`, Inter in the initramfs and no failed systemd
units. Boot: prompt -> one wrong password ("The password is incorrect.
Try again.") -> correct password -> sign-in screen.

Result: **PASS** — an encrypted installation starts, asks for the
password on the VeltOS boot screen and reaches the desktop.
