# VeltOS boot test — secureboot — PASS

- **iso**: veltos-0.1.0-dev-amd64.hybrid.iso
- **iso_sha256**: ef58a6b5d67b7b620f8817a1293c9ebe87c83fcda9ff6216c1a0ef90c70dcd2c
- **firmware**: secureboot
- **vm**: QEMU/KVM q35, 4 vCPU (host CPU model), 4096 MiB RAM, virtio-vga 1920x1080 (no 3D acceleration), virtio-net
- **qemu**: QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)
- **started_utc**: 20261026-070128
- **duration_s**: 96.5

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | boot menu drawn | screenshot 84386 bytes |
| PASS | guest agent reachable (system booted) | after 11.3s |
| PASS | os-release identifies VeltOS | PRETTY_NAME="VeltOS 0.1 (pre-alpha)"; NAME="VeltOS"; VERSION_ID="0.1"; VERSION="0.1 (pre-alpha)"; VERSION_CODENAME=trixie; ID=veltos; ID_LIKE=debian; ANSI_COLOR="38;2;79;124;255"; LOGO=veltos-logo; HOME_URL="https://veltos.ahmetfurkandemir.com/"; SUPPORT_URL="https://veltos.ahmetfurkandemir.com/"; |
| PASS | VeltOS packages installed | linux-image-amd64 6.12.113-1 plasma-workspace 4:6.3.6-2 veltos-auth 0.1.0~dev1 veltos-base 0.1.0~dev1 veltos-clock 0.1.0~dev1 veltos-desktop 0.1.0~dev1 veltos-explorer 0.1.0~dev1 |
| PASS | plasmashell running for live user | after 16.3s |
| PASS | graphical session is Wayland | Name=velt; Type=wayland; State=active; Name=velt; Type=unspecified; State=active; |
| PASS | no failed systemd units | running |
| PASS | VeltOS taskbar layout applied | 2 panel spacers, icon tasks, VeltOS Start menu |
| PASS | VeltOS wallpaper set |  |
| PASS | taskbar launcher .desktop files exist | ok veltos-explorer ok firefox-esr ok org.kde.konsole ok veltos-settings |
| PASS | boot splash (VeltOS Plymouth theme) is in the live initramfs | 1 |
| PASS | live welcome window started | 1890 |
| PASS | session uses VeltOS application names (XDG_DATA_DIRS) | XDG_DATA_DIRS=/var/lib/veltos/xdg:/usr/local/share:/usr/share |
| PASS | VeltOS File Explorer only (no Dolphin); KDE System Settings hidden | Name=File Explorer; 1; un |
| PASS | per-user defaults: VeltOS style, File Explorer side bar, no live screen lock | [General]; theme=VeltOS; 1; Autolock=false; |
| PASS | VeltOS password prompt and Clock alarms run with the session; portal file dialogs | veltos-agent; clock-agent; org.freedesktop.impl.portal.FileChooser=veltos; 1; |
| PASS | booted via UEFI | efi |
| PASS | Secure Boot enabled in guest | SecureBoot enabled |
| PASS | no crashed processes | none |
| PASS | AppArmor profiles loaded from the build-time cache | apparmor.service took 0.0 s |

## Measurements

- **guest_agent_ready_s**: 11.3
### os-release

```
PRETTY_NAME="VeltOS 0.1 (pre-alpha)"
NAME="VeltOS"
VERSION_ID="0.1"
VERSION="0.1 (pre-alpha)"
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
veltos-auth 0.1.0~dev1
veltos-base 0.1.0~dev1
veltos-clock 0.1.0~dev1
veltos-desktop 0.1.0~dev1
veltos-explorer 0.1.0~dev1
```

- **plasmashell_running_s**: 16.3
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
[    4.877213] veltos adduser[1156]: The group `powerdev' does not exist.
[    4.903369] veltos adduser[1158]: The group `scanner' does not exist.
[    4.957745] veltos adduser[1167]: The group `debian-tor' does not exist.
[   12.270087] veltos obexd[2025]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
[   12.272126] veltos obexd[2025]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
```

- **systemd_analyze**: Startup finished in 2.385s (kernel) + 3.321s (userspace) = 5.706s
### systemd_analyze_blame_top10

```
1.081s live-config.service
 425ms dev-sr0.device
 346ms console-setup.service
 294ms udisks2.service
 287ms NetworkManager.service
 237ms accounts-daemon.service
 229ms dev-loop0.device
 205ms polkit.service
 168ms avahi-daemon.service
 142ms user@1000.service
```

### free_m

```
               total        used        free      shared  buff/cache   available
Mem:            3883        1541        1390         134        1298        2341
Swap:              0           0           0
```

- **idle_used_mib(MemTotal-MemAvailable)**: 1541
- **shmem_mib(live overlay tmpfs etc.)**: 134
### top_processes_by_rss

```
  685.2 MiB  plasmashell
  350.4 MiB  kwin_wayland
  153.7 MiB  kded6
  135.7 MiB  org_kde_powerde
  135.5 MiB  kactivitymanage
  134.1 MiB  xdg-desktop-por
  127.0 MiB  kaccess
  122.4 MiB  ksmserver
  121.2 MiB  xembedsniproxy
  120.4 MiB  gmenudbusmenupr
   79.9 MiB  Xwayland
   79.5 MiB  veltos-explorer
   48.9 MiB  startplasma-way
   33.0 MiB  veltos-clock-ag
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
