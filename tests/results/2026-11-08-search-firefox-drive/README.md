# Items 166-168: see-through search fields, Firefox's downloads, the system drive

Dev VM (QEMU/KVM, no 3D, llvmpipe; installed system with the
`1.3.0~dev1` packages of veltos-desktop, veltos-settings and
veltos-explorer, user jordanl, 1920x1080), 2026-11-07/08. Crops of full
screenshots.

## Search fields (item 166)

- `start-search-dark.png`, `start-search-light.png`: Start's field while
  typing (Start always focuses it): a see-through layer on Start's acrylic,
  darker in dark mode, lighter in light mode, the accent frame.
- `search-window-dark.png`, `search-window-light.png`: the taskbar's
  search window, the accent line along the bottom.
- `settings-search-typing-dark.png`, `settings-search-typing-light.png`:
  Settings' title bar search after a click (it turned solid black or
  white before).

## Firefox's downloads (item 167)

Firefox ESR 153 (Debian 13). A 3 GB file served slowly from the VM
container (`http://10.0.2.2:8099/`) to show the progress.

- `firefox-panel-dark.png`, `firefox-panel-light.png`: the downloads panel
  with its heading, rounded rows and the thin accent progress line.
- `firefox-library-dark.png`, `firefox-library-light.png`: "Show all
  downloads" (the Library window): window colours, frameless toolbar,
  roomy navigation rows, the list on a rounded card, the selected row in an
  accent tint with the accent progress line (before the namespace fix the
  line was in the text colour: the sheet's default namespace is XUL's and
  Firefox's progress bar is an HTML element).

## The system drive (item 168)

- `this-pc-before.png`: 1.2.0 File Explorer on an unencrypted system
  ("Local Disk").
- `this-pc-encrypted-volume.png`: 1.3.0~dev1 with an unlocked LUKS volume
  (a 300 MB file on a loop device, `cryptsetup luksFormat` + `open`, ext4
  "Secret", mounted at /mnt/secret): the system drive "Local Disk (VeltOS)"
  and the encrypted volume. The same lsblk tree with release 1.2's
  `places.py` (`git show v1.2:...`) listed only `/dev/vda3`: lsblk reports
  the unlocked volume as type `crypt`, which 1.2 left out, so an installation
  made with "Encrypt system" had no system drive in This PC.
