# calamares-settings-veltos

The VeltOS installer: configuration and branding for
[Calamares](https://calamares.io) as shipped in the live ISO. Replaces
Debian's `calamares-settings-debian` (from which the configuration and
helper scripts are derived, ISC licence).

## What the user sees

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

## Tests

`tests/test_config.py` (package build): YAML validity, every sequence step
is a known Calamares module or a shipped job, job scripts exist and pass
`sh -n`, and no user-visible installer string mentions Debian.

Status: **installation not yet tested end to end** — see `docs/status.md`.
