# calamares-settings-veltos

The VeltOS installer: configuration and branding for
[Calamares](https://calamares.io) as shipped in the live ISO. Replaces
Debian's `calamares-settings-debian` (from which the configuration and
helper scripts are derived, ISC licence).

## What the user sees

- When the live system starts, a **welcome window**: "Try VeltOS"
  (closes the window) or "Install VeltOS" (starts the installer), and an
  English / Türkçe switch in the corner. Switching writes the language and
  keyboard layout for the session (`plasma-localerc`, `kxkbrc`) and signs
  out; SDDM signs the live user in again at once (`Relogin=true` from
  `/etc/sddm.conf.d/veltos-live.conf`), now in that language. The boot
  menu therefore has no separate Turkish entry. Shown only on the install
  medium.
- In the live session the screen never locks, dims or turns off and the
  computer does not go to sleep (nobody knows the live user's password).
- An "Install VeltOS" icon on the live desktop and in the Start menu
  ("VeltOS'u Kur" in Turkish).
- Calamares with VeltOS name, logo, colours and a slideshow (English and
  Turkish) while files are copied. No Debian branding anywhere.
- A confirmation prompt before anything is written to disk.

## What it does differently from Debian's settings

| Area | VeltOS behaviour | Why |
|---|---|---|
| UEFI bootloader | Installs `grub-efi-amd64-signed` + `shim-signed` | Installed systems boot with Secure Boot on (Debian's helper installs unsigned GRUB only) |
| EFI directory | Stays `\EFI\debian\` (`efiBootloaderId`) | Debian's signed GRUB looks for its config there; another name breaks Secure Boot |
| Firmware boot entry | Renamed to "VeltOS" by the `efi-label` job | Users see VeltOS in the firmware boot menu (F12 etc.) |
| Disk encryption password tries | `crypttab-tries` job adds `tries=0` to the installed system's crypttab entries unlocked with a typed password | The start-up screen asks until the password is right, like Windows, instead of dropping to a recovery shell after three wrong tries (cryptsetup's default). Calamares' fstab module writes those entries without options when /boot is unencrypted, so `crypttabOptions` cannot do it. |
| Dual boot | `os-prober` installed, `GRUB_DISABLE_OS_PROBER=false` | Windows appears in the boot menu |
| Offline install | Bootloader packages come from the ISO's package pool (`veltos-installer.list.binary`) | Installs work without network |
| APT sources | `main contrib non-free non-free-firmware` for trixie, -updates, -security | Needed for NVIDIA drivers and Steam later |
| Requirements | 20 GB disk, 2 GB RAM | Realistic for a Plasma desktop plus apps |
| Removed after install | live packages, Calamares and this package | Installed system has no installer leftovers |

## Layout

| Path | Installed to |
|---|---|
| `calamares/settings.conf`, `calamares/modules/*.conf` | `/etc/calamares/` |
| `calamares/branding/veltos/` (+ rendered `logo.png`, `welcome.png` link to the wallpaper) | `/etc/calamares/branding/veltos/` |
| `modules/*/module.desc` (custom jobs) | `/usr/lib/calamares/modules/` |
| `helpers/*` (job scripts) | `/usr/libexec/veltos-installer/` |
| `bin/install-veltos`, `bin/veltos-install-desktop-icon` | `/usr/bin/` |
| `data/install-veltos.desktop` / `veltos-install-icon.desktop` | `/usr/share/applications/` / `/etc/xdg/autostart/` |
| `welcome/veltos-live-welcome`, `welcome/Main.qml` | `/usr/libexec/veltos-installer/`, `/usr/share/veltos-live-welcome/` (PySide6 + QML) |
| `data/veltos-live-welcome.desktop` | `/etc/xdg/autostart/` and `/usr/share/applications/` (hidden; gives the window its icon) |
| `data/veltos-live-session.sh` | `/etc/xdg/plasma-workspace/env/` (live-only: no lock, no sleep, no screen off) |
| `data/veltos-live.conf` | `/etc/sddm.conf.d/` (live-only: sign in again after signing out) |

## Tests

`tests/test_config.py` (package build): YAML validity, every sequence step
is a known Calamares module or a shipped job, job scripts exist and pass
`sh -n`, and no user-visible installer string mentions Debian.
`tests/test_welcome.py`: language detection, complete translations, the
welcome window loads offscreen without QML warnings, and the live session
script writes the no-lock/no-sleep settings only on the install medium.

`tests/test_efi_label.py` and `tests/test_crypttab_tries.py` run the job
scripts against fake firmware output and a fake target root.

Status: an installation with "Encrypt system" (UEFI, VM) was tested end to
end on 2026-10-19 (`tests/results/2026-10-19-encrypted-install-uefi/`);
plain and BIOS installations are not yet tested — see `docs/status.md`.
