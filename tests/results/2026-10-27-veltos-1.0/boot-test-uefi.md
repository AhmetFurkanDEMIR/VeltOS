# VeltOS boot test — uefi — PASS

- **iso**: veltos-1.0-amd64.hybrid.iso
- **iso_sha256**: 3e5273a13b0f87a11bd6a3fb668674b02c5865264065dfe5e570387f4ac1a2af
- **firmware**: uefi
- **vm**: QEMU/KVM q35, 4 vCPU (host CPU model), 4096 MiB RAM, virtio-vga 1920x1080 (no 3D acceleration), virtio-net
- **qemu**: QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)
- **started_utc**: 20261027-073732
- **duration_s**: 110.3

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | boot menu drawn | screenshot 84713 bytes |
| PASS | guest agent reachable (system booted) | after 15.0s |
| PASS | os-release identifies VeltOS | PRETTY_NAME="VeltOS 1.0"; NAME="VeltOS"; VERSION_ID="1.0"; VERSION="1.0"; VERSION_CODENAME=trixie; ID=veltos; ID_LIKE=debian; ANSI_COLOR="38;2;79;124;255"; LOGO=veltos-logo; HOME_URL="https://veltos.ahmetfurkandemir.com/"; SUPPORT_URL="https://veltos.ahmetfurkandemir.com/"; |
| PASS | VeltOS packages installed | linux-image-amd64 6.12.113-1 plasma-workspace 4:6.3.6-2 veltos-auth 1.0.0 veltos-base 1.0.0 veltos-clock 1.0.0 veltos-desktop 1.0.0 veltos-explorer 1.0.0 |
| PASS | plasmashell running for live user | after 30.6s |
| PASS | graphical session is Wayland | Name=velt; Type=wayland; State=active; Name=velt; Type=unspecified; State=active; |
| PASS | no failed systemd units | running |
| PASS | VeltOS taskbar layout applied | 2 panel spacers, icon tasks, VeltOS Start menu |
| PASS | VeltOS wallpaper set |  |
| PASS | taskbar launcher .desktop files exist | ok veltos-explorer ok firefox-esr ok org.kde.konsole ok veltos-settings |
| PASS | boot splash (VeltOS Plymouth theme) is in the live initramfs | 1 |
| PASS | live welcome window started | 1907 |
| PASS | session uses VeltOS application names (XDG_DATA_DIRS) | XDG_DATA_DIRS=/var/lib/veltos/xdg:/usr/local/share:/usr/share |
| PASS | VeltOS File Explorer only (no Dolphin); KDE System Settings hidden | Name=File Explorer; 1; un |
| PASS | per-user defaults: VeltOS style, File Explorer side bar, no live screen lock | [General]; theme=VeltOS; 1; Autolock=false; |
| PASS | VeltOS password prompt and Clock alarms run with the session; portal file dialogs | veltos-agent; clock-agent; org.freedesktop.impl.portal.FileChooser=veltos; 1; |
| PASS | booted via UEFI | efi |
| PASS | no crashed processes | none |
| PASS | AppArmor profiles loaded from the build-time cache | apparmor.service took 0.0 s |

## Measurements

- **guest_agent_ready_s**: 15.0
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
[    8.908568] veltos adduser[1167]: The group `powerdev' does not exist.
[    8.935884] veltos adduser[1169]: The group `scanner' does not exist.
[    8.991554] veltos adduser[1178]: The group `debian-tor' does not exist.
[   26.695373] veltos obexd[2050]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
[   26.696578] veltos obexd[2050]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
```

- **systemd_analyze**: Startup finished in 4.949s (kernel) + 5.762s (userspace) = 10.712s
### systemd_analyze_blame_top10

```
2.432s live-config.service
1.043s NetworkManager.service
 855ms udisks2.service
 775ms lm-sensors.service
 731ms console-setup.service
 685ms dev-sr0.device
 578ms accounts-daemon.service
 511ms polkit.service
 379ms e2scrub_reap.service
 362ms systemd-logind.service
```

### free_m

```
               total        used        free      shared  buff/cache   available
Mem:            3915        1540        1476         134        1251        2374
Swap:           1957           0        1957
```

- **idle_used_mib(MemTotal-MemAvailable)**: 1541
- **shmem_mib(live overlay tmpfs etc.)**: 134
### top_processes_by_rss

```
  670.7 MiB  plasmashell
  347.9 MiB  kwin_wayland
  153.6 MiB  kded6
  135.9 MiB  kactivitymanage
  135.8 MiB  org_kde_powerde
  134.4 MiB  xdg-desktop-por
  127.0 MiB  kaccess
  122.3 MiB  ksmserver
  121.8 MiB  gmenudbusmenupr
  121.4 MiB  xembedsniproxy
   80.7 MiB  Xwayland
   78.9 MiB  veltos-explorer
   48.8 MiB  startplasma-way
   33.0 MiB  veltos-clock-ag
   31.5 MiB  veltos-auth-age
```

- **process_count**: 177
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
