# VeltOS boot test — secureboot — PASS

- **iso**: veltos-0.1.0-dev-amd64.hybrid.iso
- **iso_sha256**: 9d8afa183a94975fa43db82708bb095b6e23e40a527e5733b7c01cc196d32464
- **firmware**: secureboot
- **vm**: QEMU/KVM q35, 4 vCPU (host CPU model), 4096 MiB RAM, virtio-vga 1920x1080 (no 3D acceleration), virtio-net
- **qemu**: QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)
- **started_utc**: 20261023-063808
- **duration_s**: 96.4

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | boot menu drawn | screenshot 84280 bytes |
| PASS | guest agent reachable (system booted) | after 11.0s |
| PASS | os-release identifies VeltOS | PRETTY_NAME="VeltOS 0.1 (pre-alpha)"; NAME="VeltOS"; VERSION_ID="0.1"; VERSION="0.1 (pre-alpha)"; VERSION_CODENAME=trixie; ID=veltos; ID_LIKE=debian; ANSI_COLOR="38;2;79;124;255"; LOGO=veltos-logo; HOME_URL="https://veltos.ahmetfurkandemir.com/"; SUPPORT_URL="https://veltos.ahmetfurkandemir.com/"; |
| PASS | VeltOS packages installed | linux-image-amd64 6.12.113-1 plasma-workspace 4:6.3.6-2 veltos-auth 0.1.0~dev1 veltos-base 0.1.0~dev1 veltos-clock 0.1.0~dev1 veltos-desktop 0.1.0~dev1 veltos-explorer 0.1.0~dev1 |
| PASS | plasmashell running for live user | after 16.0s |
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
| PASS | booted via UEFI | efi |
| PASS | Secure Boot enabled in guest | SecureBoot enabled |
| PASS | no crashed processes | none |
| PASS | AppArmor profiles loaded from the build-time cache | apparmor.service took 0.0 s |

## Measurements

- **guest_agent_ready_s**: 11.0
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

- **plasmashell_running_s**: 16.0
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
[    4.744130] veltos adduser[1158]: The group `powerdev' does not exist.
[    4.769937] veltos adduser[1160]: The group `scanner' does not exist.
[    4.826387] veltos adduser[1169]: The group `debian-tor' does not exist.
[   11.461219] veltos obexd[2011]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
[   11.462077] veltos obexd[2011]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
```

- **systemd_analyze**: Startup finished in 2.385s (kernel) + 3.322s (userspace) = 5.708s
### systemd_analyze_blame_top10

```
1.148s live-config.service
 415ms dev-sr0.device
 336ms console-setup.service
 333ms NetworkManager.service
 280ms udisks2.service
 229ms dev-loop0.device
 182ms accounts-daemon.service
 152ms ModemManager.service
 151ms dbus.service
 135ms polkit.service
```

### free_m

```
               total        used        free      shared  buff/cache   available
Mem:            3883        1522        1419         133        1287        2361
Swap:              0           0           0
```

- **idle_used_mib(MemTotal-MemAvailable)**: 1522
- **shmem_mib(live overlay tmpfs etc.)**: 133
### top_processes_by_rss

```
  674.5 MiB  plasmashell
  348.8 MiB  kwin_wayland
  152.0 MiB  kded6
  135.8 MiB  org_kde_powerde
  135.3 MiB  kactivitymanage
  134.6 MiB  xdg-desktop-por
  127.4 MiB  kaccess
  122.5 MiB  ksmserver
  121.3 MiB  gmenudbusmenupr
  120.7 MiB  xembedsniproxy
   81.0 MiB  Xwayland
   76.1 MiB  veltos-explorer
   48.9 MiB  startplasma-way
   32.8 MiB  veltos-clock-ag
   31.9 MiB  veltos-auth-age
```

- **process_count**: 173
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
