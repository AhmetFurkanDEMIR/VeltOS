# 2026-10-31 — A Turkish installation with Bottles: first start, Bottles, the VeltOS bottle

Dev VM (QEMU/KVM, UEFI, 8 GB, 40 GB virtio disk, network on), ISO
`veltos-1.1-dev4` with calamares-settings-veltos 1.1.0~dev2 installed into
the live system first (the language order below), then veltos-winapps
1.1.0~dev2 rebuilt and installed into the installed system for `07`.

- `01`: the installer's language list: Türkçe (Türkiye) first, American
  English second (before: Arabic first, Türkçe in the middle; item 38).
- `02`: the "Windows programs" step; Bottles chosen. "Erase disk", account
  "Ahmet Test" (`ahmett`), no automatic sign-in.
- `03`: the installation finished ("VeltOS hazır"), about 12 minutes.
- First start of the installed system (item 98): `veltos-first-update`
  ran `apt-get update` (all 75 lists fetched, `/var/log/veltos-first-update.log`),
  found nothing to upgrade (the image was built the same day) and installed
  Bottles system-wide from Flathub (`/etc/veltos/windows-apps.conf`
  `runner=bottles`; Bottles 67.5 with its runtimes, about 300 MB). `04`:
  after signing in, the full-screen "Her şeyi sizin için hazırlıyoruz"
  window with "Windows programları için Bottles yükleniyor…"; it closed by
  itself when the work was done (`/var/lib/veltos/first-update-done`),
  `05`: the desktop.
- Sign-in set-up (item 100): `veltos-run --bottles-setup` made the
  "VeltOS" bottle (`bottles-cli new`, Soda 11.0-10, about two minutes).
- `06`: a double-click on `putty.exe` (PuTTY 0.85 from the publisher's
  site, SHA-256 d01fdb5a...26c87) the old way handed the file to Bottles'
  window, which asked "Şişe Seç" (Select Bottle) every time; PuTTY ran
  after "Seç".
- `07`: with the new hand-off (`bottles-cli run -b VeltOS -e` through
  flatpak's `--file-forwarding`) PuTTY opened straight in the VeltOS bottle.

Not tried here: an installation without network (Bottles then waits for
the next starts, five tries), a Windows installer (.msi/setup.exe) in
Bottles.
