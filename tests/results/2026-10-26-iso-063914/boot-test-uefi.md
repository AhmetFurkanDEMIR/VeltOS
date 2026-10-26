# VeltOS boot test — uefi — PASS

- **iso**: veltos-0.1.0-dev-amd64.hybrid.iso
- **iso_sha256**: ef58a6b5d67b7b620f8817a1293c9ebe87c83fcda9ff6216c1a0ef90c70dcd2c
- **firmware**: uefi
- **vm**: QEMU/KVM q35, 4 vCPU (host CPU model), 4096 MiB RAM, virtio-vga 1920x1080 (no 3D acceleration), virtio-net
- **qemu**: QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)
- **started_utc**: 20261026-065717
- **duration_s**: 100.2

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | boot menu drawn | screenshot 84831 bytes |
| PASS | guest agent reachable (system booted) | after 11.9s |
| PASS | os-release identifies VeltOS | PRETTY_NAME="VeltOS 0.1 (pre-alpha)"; NAME="VeltOS"; VERSION_ID="0.1"; VERSION="0.1 (pre-alpha)"; VERSION_CODENAME=trixie; ID=veltos; ID_LIKE=debian; ANSI_COLOR="38;2;79;124;255"; LOGO=veltos-logo; HOME_URL="https://veltos.ahmetfurkandemir.com/"; SUPPORT_URL="https://veltos.ahmetfurkandemir.com/"; |
| PASS | VeltOS packages installed | linux-image-amd64 6.12.113-1 plasma-workspace 4:6.3.6-2 veltos-auth 0.1.0~dev1 veltos-base 0.1.0~dev1 veltos-clock 0.1.0~dev1 veltos-desktop 0.1.0~dev1 veltos-explorer 0.1.0~dev1 |
| PASS | plasmashell running for live user | after 20.5s |
| PASS | graphical session is Wayland | Name=velt; Type=wayland; State=active; Name=velt; Type=unspecified; State=active; |
| PASS | no failed systemd units | running |
| PASS | VeltOS taskbar layout applied | 2 panel spacers, icon tasks, VeltOS Start menu |
| PASS | VeltOS wallpaper set |  |
| PASS | taskbar launcher .desktop files exist | ok veltos-explorer ok firefox-esr ok org.kde.konsole ok veltos-settings |
| PASS | boot splash (VeltOS Plymouth theme) is in the live initramfs | 1 |
| PASS | live welcome window started | 1888 |
| PASS | session uses VeltOS application names (XDG_DATA_DIRS) | XDG_DATA_DIRS=/var/lib/veltos/xdg:/usr/local/share:/usr/share |
| PASS | VeltOS File Explorer only (no Dolphin); KDE System Settings hidden | Name=File Explorer; 1; un |
| PASS | per-user defaults: VeltOS style, File Explorer side bar, no live screen lock | [General]; theme=VeltOS; 1; Autolock=false; |
| PASS | VeltOS password prompt and Clock alarms run with the session; portal file dialogs | veltos-agent; clock-agent; org.freedesktop.impl.portal.FileChooser=veltos; 1; |
| PASS | booted via UEFI | efi |
| PASS | no crashed processes | none |
| PASS | AppArmor profiles loaded from the build-time cache | apparmor.service took 0.0 s |

## Measurements

- **guest_agent_ready_s**: 11.9
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

- **plasmashell_running_s**: 20.5
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
[    5.393710] veltos adduser[1155]: The group `powerdev' does not exist.
[    5.419728] veltos adduser[1157]: The group `scanner' does not exist.
[    5.480366] veltos adduser[1166]: The group `debian-tor' does not exist.
[   14.651875] veltos obexd[2018]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
[   14.652575] veltos obexd[2018]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
```

- **systemd_analyze**: Startup finished in 3.041s (kernel) + 3.256s (userspace) = 6.298s
### systemd_analyze_blame_top10

```
1.135s live-config.service
 414ms dev-sr0.device
 367ms NetworkManager.service
 333ms udisks2.service
 327ms console-setup.service
 233ms dev-loop0.device
 214ms ModemManager.service
 181ms accounts-daemon.service
 176ms user@1000.service
 148ms avahi-daemon.service
```

### free_m

```
               total        used        free      shared  buff/cache   available
Mem:            3915        1538        1433         134        1297        2377
Swap:              0           0           0
```

- **idle_used_mib(MemTotal-MemAvailable)**: 1538
- **shmem_mib(live overlay tmpfs etc.)**: 134
### top_processes_by_rss

```
  668.0 MiB  plasmashell
  359.8 MiB  kwin_wayland
  153.6 MiB  kded6
  135.6 MiB  org_kde_powerde
  135.5 MiB  kactivitymanage
  134.5 MiB  xdg-desktop-por
  127.1 MiB  kaccess
  122.2 MiB  ksmserver
  121.2 MiB  xembedsniproxy
  120.9 MiB  gmenudbusmenupr
   79.9 MiB  Xwayland
   79.8 MiB  veltos-explorer
   49.0 MiB  startplasma-way
   32.9 MiB  veltos-clock-ag
   31.6 MiB  veltos-auth-age
```

- **process_count**: 176
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
