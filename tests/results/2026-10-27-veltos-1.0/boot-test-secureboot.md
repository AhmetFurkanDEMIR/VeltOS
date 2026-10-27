# VeltOS boot test — secureboot — PASS

- **iso**: veltos-1.0-amd64.hybrid.iso
- **iso_sha256**: 3e5273a13b0f87a11bd6a3fb668674b02c5865264065dfe5e570387f4ac1a2af
- **firmware**: secureboot
- **vm**: QEMU/KVM q35, 4 vCPU (host CPU model), 4096 MiB RAM, virtio-vga 1920x1080 (no 3D acceleration), virtio-net
- **qemu**: QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)
- **started_utc**: 20261027-074147
- **duration_s**: 112.0

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | boot menu drawn | screenshot 84269 bytes |
| PASS | guest agent reachable (system booted) | after 15.1s |
| PASS | os-release identifies VeltOS | PRETTY_NAME="VeltOS 1.0"; NAME="VeltOS"; VERSION_ID="1.0"; VERSION="1.0"; VERSION_CODENAME=trixie; ID=veltos; ID_LIKE=debian; ANSI_COLOR="38;2;79;124;255"; LOGO=veltos-logo; HOME_URL="https://veltos.ahmetfurkandemir.com/"; SUPPORT_URL="https://veltos.ahmetfurkandemir.com/"; |
| PASS | VeltOS packages installed | linux-image-amd64 6.12.113-1 plasma-workspace 4:6.3.6-2 veltos-auth 1.0.0 veltos-base 1.0.0 veltos-clock 1.0.0 veltos-desktop 1.0.0 veltos-explorer 1.0.0 |
| PASS | plasmashell running for live user | after 30.6s |
| PASS | graphical session is Wayland | Name=velt; Type=wayland; State=active; Name=velt; Type=unspecified; State=active; |
| PASS | no failed systemd units | running |
| PASS | VeltOS taskbar layout applied | 2 panel spacers, icon tasks, VeltOS Start menu |
| PASS | VeltOS wallpaper set |  |
| PASS | taskbar launcher .desktop files exist | ok veltos-explorer ok firefox-esr ok org.kde.konsole ok veltos-settings |
| PASS | boot splash (VeltOS Plymouth theme) is in the live initramfs | 1 |
| PASS | live welcome window started | 1886 |
| PASS | session uses VeltOS application names (XDG_DATA_DIRS) | XDG_DATA_DIRS=/var/lib/veltos/xdg:/usr/local/share:/usr/share |
| PASS | VeltOS File Explorer only (no Dolphin); KDE System Settings hidden | Name=File Explorer; 1; un |
| PASS | per-user defaults: VeltOS style, File Explorer side bar, no live screen lock | [General]; theme=VeltOS; 1; Autolock=false; |
| PASS | VeltOS password prompt and Clock alarms run with the session; portal file dialogs | veltos-agent; clock-agent; org.freedesktop.impl.portal.FileChooser=veltos; 1; |
| PASS | booted via UEFI | efi |
| PASS | Secure Boot enabled in guest | SecureBoot enabled |
| PASS | no crashed processes | none |
| PASS | AppArmor profiles loaded from the build-time cache | apparmor.service took 0.0 s |

## Measurements

- **guest_agent_ready_s**: 15.1
### os-release

```
PRETTY_NAME="VeltOS 1.0"
NAME="VeltOS"
VERSION_ID="1.0"
VERSION="1.0"
VERSION_CODENAME=trixie
ID=veltos
ID_LIKE=debian
ANSI_COLOR="38;2;79;124;255"
LOGO=veltos-logo
HOME_URL="https://veltos.ahmetfurkandemir.com/"
SUPPORT_URL="https://veltos.ahmetfurkandemir.com/"
```

### key_packages

```
linux-image-amd64 6.12.113-1
plasma-workspace 4:6.3.6-2
veltos-auth 1.0.0
veltos-base 1.0.0
veltos-clock 1.0.0
veltos-desktop 1.0.0
veltos-explorer 1.0.0
```

- **plasmashell_running_s**: 30.6
### sessions

```
Name=velt
Type=wayland
State=active
Name=velt
Type=unspecified
State=active
```

### journal_errors_tail

```
[    8.707069] veltos adduser[1170]: The group `powerdev' does not exist.
[    8.732406] veltos adduser[1172]: The group `scanner' does not exist.
[    8.786116] veltos adduser[1181]: The group `debian-tor' does not exist.
[   27.321447] veltos obexd[2059]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
[   27.324561] veltos obexd[2059]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
```

- **systemd_analyze**: Startup finished in 4.691s (kernel) + 5.884s (userspace) = 10.576s
### systemd_analyze_blame_top10

```
2.436s live-config.service
 866ms udisks2.service
 799ms NetworkManager.service
 753ms dev-sr0.device
 707ms console-setup.service
 525ms accounts-daemon.service
 492ms avahi-daemon.service
 488ms lm-sensors.service
 457ms polkit.service
 432ms dbus.service
```

### free_m

```
               total        used        free      shared  buff/cache   available
Mem:            3883        1554        1423         134        1252        2328
Swap:           1941           0        1941
```

- **idle_used_mib(MemTotal-MemAvailable)**: 1554
- **shmem_mib(live overlay tmpfs etc.)**: 134
### top_processes_by_rss

```
  679.1 MiB  plasmashell
  349.2 MiB  kwin_wayland
  154.0 MiB  kded6
  136.1 MiB  kactivitymanage
  135.8 MiB  org_kde_powerde
  134.3 MiB  xdg-desktop-por
  126.9 MiB  kaccess
  122.5 MiB  ksmserver
  121.5 MiB  gmenudbusmenupr
  121.1 MiB  xembedsniproxy
   80.7 MiB  Xwayland
   79.6 MiB  veltos-explorer
   49.0 MiB  startplasma-way
   32.9 MiB  veltos-clock-ag
   31.7 MiB  veltos-auth-age
```

- **process_count**: 178
### kernel_and_gpu

```
6.12.113+deb13-amd64
00:02.0 VGA compatible controller: Red Hat, Inc. Virtio 1.0 GPU (rev 01)
	Subsystem: Red Hat, Inc. QEMU
	Kernel driver in use: virtio-pci
```


## Screenshots

- boot menu: `01-boot-menu.png`
- boot splash: `01b-boot-splash.png`
- desktop (with the live welcome window): `02-desktop.png`
- desktop without welcome window: `03-desktop-clean.png`
- start menu: `04-start-menu.png`
