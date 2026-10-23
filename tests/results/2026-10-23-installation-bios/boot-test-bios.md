# VeltOS boot test — bios — PASS

- **iso**: veltos-0.1.0-dev-amd64.hybrid.iso
- **iso_sha256**: 9d8afa183a94975fa43db82708bb095b6e23e40a527e5733b7c01cc196d32464
- **firmware**: bios
- **vm**: QEMU/KVM q35, 4 vCPU (host CPU model), 4096 MiB RAM, virtio-vga 1920x1080 (no 3D acceleration), virtio-net
- **qemu**: QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)
- **started_utc**: 20261023-063609
- **duration_s**: 98.6

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | boot menu drawn | screenshot 16253 bytes |
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
| PASS | live welcome window started | 1875 |
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
[    4.811371] veltos adduser[1153]: The group `powerdev' does not exist.
[    4.838410] veltos adduser[1155]: The group `scanner' does not exist.
[    4.893382] veltos adduser[1164]: The group `debian-tor' does not exist.
[   11.907609] veltos obexd[1994]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
[   11.908281] veltos obexd[1994]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
```

- **systemd_analyze**: Startup finished in 2.401s (kernel) + 3.214s (userspace) = 5.615s
### systemd_analyze_blame_top10

```
1.150s live-config.service
 452ms dev-sr0.device
 333ms console-setup.service
 292ms udisks2.service
 285ms NetworkManager.service
 212ms dev-loop0.device
 180ms accounts-daemon.service
 162ms ModemManager.service
 156ms dbus.service
 142ms plymouth-start.service
```

### free_m

```
               total        used        free      shared  buff/cache   available
Mem:            3921        1505        1481         133        1287        2415
Swap:              0           0           0
```

- **idle_used_mib(MemTotal-MemAvailable)**: 1506
- **shmem_mib(live overlay tmpfs etc.)**: 133
### top_processes_by_rss

```
  665.6 MiB  plasmashell
  350.8 MiB  kwin_wayland
  151.9 MiB  kded6
  136.6 MiB  kactivitymanage
  135.9 MiB  org_kde_powerde
  134.0 MiB  xdg-desktop-por
  127.1 MiB  kaccess
  122.7 MiB  ksmserver
  121.6 MiB  xembedsniproxy
  120.9 MiB  gmenudbusmenupr
   80.0 MiB  Xwayland
   77.0 MiB  veltos-explorer
   49.0 MiB  startplasma-way
   32.9 MiB  veltos-clock-ag
   31.3 MiB  kioworker
```

- **process_count**: 175
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
