# VeltOS boot test — bios — PASS

- **iso**: veltos-0.1.0-dev-amd64.hybrid.iso
- **iso_sha256**: ef58a6b5d67b7b620f8817a1293c9ebe87c83fcda9ff6216c1a0ef90c70dcd2c
- **firmware**: bios
- **vm**: QEMU/KVM q35, 4 vCPU (host CPU model), 4096 MiB RAM, virtio-vga 1920x1080 (no 3D acceleration), virtio-net
- **qemu**: QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)
- **started_utc**: 20261026-065922
- **duration_s**: 99.1

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | boot menu drawn | screenshot 16341 bytes |
| PASS | guest agent reachable (system booted) | after 14.9s |
| PASS | os-release identifies VeltOS | PRETTY_NAME="VeltOS 0.1 (pre-alpha)"; NAME="VeltOS"; VERSION_ID="0.1"; VERSION="0.1 (pre-alpha)"; VERSION_CODENAME=trixie; ID=veltos; ID_LIKE=debian; ANSI_COLOR="38;2;79;124;255"; LOGO=veltos-logo; HOME_URL="https://veltos.ahmetfurkandemir.com/"; SUPPORT_URL="https://veltos.ahmetfurkandemir.com/"; |
| PASS | VeltOS packages installed | linux-image-amd64 6.12.113-1 plasma-workspace 4:6.3.6-2 veltos-auth 0.1.0~dev1 veltos-base 0.1.0~dev1 veltos-clock 0.1.0~dev1 veltos-desktop 0.1.0~dev1 veltos-explorer 0.1.0~dev1 |
| PASS | plasmashell running for live user | after 19.9s |
| PASS | graphical session is Wayland | Name=velt; Type=wayland; State=active; Name=velt; Type=unspecified; State=active; |
| PASS | no failed systemd units | running |
| PASS | VeltOS taskbar layout applied | 2 panel spacers, icon tasks, VeltOS Start menu |
| PASS | VeltOS wallpaper set |  |
| PASS | taskbar launcher .desktop files exist | ok veltos-explorer ok firefox-esr ok org.kde.konsole ok veltos-settings |
| PASS | boot splash (VeltOS Plymouth theme) is in the live initramfs | 1 |
| PASS | live welcome window started | 1878 |
| PASS | session uses VeltOS application names (XDG_DATA_DIRS) | XDG_DATA_DIRS=/var/lib/veltos/xdg:/usr/local/share:/usr/share |
| PASS | VeltOS File Explorer only (no Dolphin); KDE System Settings hidden | Name=File Explorer; 1; un |
| PASS | per-user defaults: VeltOS style, File Explorer side bar, no live screen lock | [General]; theme=VeltOS; 1; Autolock=false; |
| PASS | VeltOS password prompt and Clock alarms run with the session; portal file dialogs | veltos-agent; clock-agent; org.freedesktop.impl.portal.FileChooser=veltos; 1; |
| PASS | no crashed processes | none |
| PASS | AppArmor profiles loaded from the build-time cache | apparmor.service took 0.0 s |

## Measurements

- **guest_agent_ready_s**: 14.9
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

- **plasmashell_running_s**: 19.9
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
[    4.776346] veltos adduser[1152]: The group `powerdev' does not exist.
[    4.802687] veltos adduser[1154]: The group `scanner' does not exist.
[    4.859315] veltos adduser[1163]: The group `debian-tor' does not exist.
[   12.700307] veltos obexd[2010]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
[   12.701099] veltos obexd[2010]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
```

- **systemd_analyze**: Startup finished in 2.442s (kernel) + 3.205s (userspace) = 5.648s
### systemd_analyze_blame_top10

```
1.082s live-config.service
 474ms dev-sr0.device
 350ms console-setup.service
 307ms NetworkManager.service
 299ms udisks2.service
 248ms dev-loop0.device
 190ms accounts-daemon.service
 182ms user@1000.service
 172ms avahi-daemon.service
 162ms dbus.service
```

### free_m

```
               total        used        free      shared  buff/cache   available
Mem:            3921        1540        1437         134        1298        2380
Swap:              0           0           0
```

- **idle_used_mib(MemTotal-MemAvailable)**: 1539
- **shmem_mib(live overlay tmpfs etc.)**: 134
### top_processes_by_rss

```
  677.6 MiB  plasmashell
  352.7 MiB  kwin_wayland
  153.4 MiB  kded6
  136.0 MiB  kactivitymanage
  135.7 MiB  org_kde_powerde
  133.8 MiB  xdg-desktop-por
  127.1 MiB  kaccess
  122.3 MiB  ksmserver
  121.1 MiB  xembedsniproxy
  120.9 MiB  gmenudbusmenupr
   80.1 MiB  Xwayland
   78.8 MiB  veltos-explorer
   49.0 MiB  startplasma-way
   32.8 MiB  veltos-clock-ag
   31.9 MiB  veltos-auth-age
```

- **process_count**: 174
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
