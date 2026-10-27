# VeltOS boot test — bios — PASS

- **iso**: veltos-1.0-amd64.hybrid.iso
- **iso_sha256**: 3e5273a13b0f87a11bd6a3fb668674b02c5865264065dfe5e570387f4ac1a2af
- **firmware**: bios
- **vm**: QEMU/KVM q35, 4 vCPU (host CPU model), 4096 MiB RAM, virtio-vga 1920x1080 (no 3D acceleration), virtio-net
- **qemu**: QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)
- **started_utc**: 20261027-073936
- **duration_s**: 111.2

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | boot menu drawn | screenshot 16180 bytes |
| PASS | guest agent reachable (system booted) | after 15.9s |
| PASS | os-release identifies VeltOS | PRETTY_NAME="VeltOS 1.0"; NAME="VeltOS"; VERSION_ID="1.0"; VERSION="1.0"; VERSION_CODENAME=trixie; ID=veltos; ID_LIKE=debian; ANSI_COLOR="38;2;79;124;255"; LOGO=veltos-logo; HOME_URL="https://veltos.ahmetfurkandemir.com/"; SUPPORT_URL="https://veltos.ahmetfurkandemir.com/"; |
| PASS | VeltOS packages installed | linux-image-amd64 6.12.113-1 plasma-workspace 4:6.3.6-2 veltos-auth 1.0.0 veltos-base 1.0.0 veltos-clock 1.0.0 veltos-desktop 1.0.0 veltos-explorer 1.0.0 |
| PASS | plasmashell running for live user | after 31.4s |
| PASS | graphical session is Wayland | Name=velt; Type=wayland; State=active; Name=velt; Type=unspecified; State=active; |
| PASS | no failed systemd units | running |
| PASS | VeltOS taskbar layout applied | 2 panel spacers, icon tasks, VeltOS Start menu |
| PASS | VeltOS wallpaper set |  |
| PASS | taskbar launcher .desktop files exist | ok veltos-explorer ok firefox-esr ok org.kde.konsole ok veltos-settings |
| PASS | boot splash (VeltOS Plymouth theme) is in the live initramfs | 1 |
| PASS | live welcome window started | 1906 |
| PASS | session uses VeltOS application names (XDG_DATA_DIRS) | XDG_DATA_DIRS=/var/lib/veltos/xdg:/usr/local/share:/usr/share |
| PASS | VeltOS File Explorer only (no Dolphin); KDE System Settings hidden | Name=File Explorer; 1; un |
| PASS | per-user defaults: VeltOS style, File Explorer side bar, no live screen lock | [General]; theme=VeltOS; 1; Autolock=false; |
| PASS | VeltOS password prompt and Clock alarms run with the session; portal file dialogs | veltos-agent; clock-agent; org.freedesktop.impl.portal.FileChooser=veltos; 1; |
| PASS | no crashed processes | none |
| PASS | AppArmor profiles loaded from the build-time cache | apparmor.service took 0.0 s |

## Measurements

- **guest_agent_ready_s**: 15.9
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

- **plasmashell_running_s**: 31.4
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
[    8.782486] veltos adduser[1169]: The group `powerdev' does not exist.
[    8.808637] veltos adduser[1171]: The group `scanner' does not exist.
[    8.866750] veltos adduser[1180]: The group `debian-tor' does not exist.
[   26.884635] veltos obexd[2045]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
[   26.885633] veltos obexd[2045]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
```

- **systemd_analyze**: Startup finished in 4.660s (kernel) + 6.040s (userspace) = 10.701s
### systemd_analyze_blame_top10

```
2.583s live-config.service
 941ms NetworkManager.service
 839ms udisks2.service
 738ms console-setup.service
 628ms dev-sr0.device
 573ms accounts-daemon.service
 514ms lm-sensors.service
 483ms polkit.service
 392ms plymouth-start.service
 381ms avahi-daemon.service
```

### free_m

```
               total        used        free      shared  buff/cache   available
Mem:            3921        1565        1459         134        1251        2355
Swap:           1960           0        1960
```

- **idle_used_mib(MemTotal-MemAvailable)**: 1565
- **shmem_mib(live overlay tmpfs etc.)**: 134
### top_processes_by_rss

```
  678.4 MiB  plasmashell
  348.9 MiB  kwin_wayland
  153.1 MiB  kded6
  136.0 MiB  kactivitymanage
  135.6 MiB  org_kde_powerde
  134.5 MiB  xdg-desktop-por
  128.0 MiB  kaccess
  122.4 MiB  ksmserver
  121.4 MiB  gmenudbusmenupr
  120.9 MiB  xembedsniproxy
   80.3 MiB  Xwayland
   79.1 MiB  veltos-explorer
   48.9 MiB  startplasma-way
   32.8 MiB  veltos-clock-ag
   31.7 MiB  veltos-auth-age
```

- **process_count**: 181
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
