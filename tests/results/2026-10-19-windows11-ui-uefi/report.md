# VeltOS boot test — uefi — PASS

- **iso**: veltos-0.1.0-dev-amd64.hybrid.iso
- **iso_sha256**: 7d11ec03d735d721b7865d34c650a60a6e20c637b5440bf12fcaf4d0d4653034
- **firmware**: uefi
- **vm**: QEMU/KVM q35, 4 vCPU (host CPU model), 4096 MiB RAM, virtio-vga 1920x1080 (no 3D acceleration), virtio-net
- **qemu**: QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)
- **started_utc**: 20261019-065930
- **duration_s**: 97.6

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | guest agent reachable (system booted) | after 14.1s |
| PASS | os-release identifies VeltOS | PRETTY_NAME="VeltOS 0.1 (pre-alpha)"; NAME="VeltOS"; VERSION_ID="0.1"; VERSION="0.1 (pre-alpha)"; VERSION_CODENAME=trixie; ID=veltos; ID_LIKE=debian; ANSI_COLOR="38;2;79;124;255"; LOGO=veltos-logo; |
| PASS | VeltOS packages installed | linux-image-amd64 6.12.113-1 plasma-workspace 4:6.3.6-2 veltos-base 0.1.0~dev1 veltos-desktop 0.1.0~dev1 |
| PASS | plasmashell running for live user | after 19.1s |
| PASS | graphical session is Wayland | Name=velt; Type=wayland; State=active; Name=velt; Type=unspecified; State=active; |
| PASS | no failed systemd units | running |
| PASS | VeltOS taskbar layout applied | 2 panel spacers, icon tasks, VeltOS Start menu |
| PASS | VeltOS wallpaper set |  |
| PASS | taskbar launcher .desktop files exist | ok org.kde.dolphin ok firefox-esr ok org.kde.konsole ok veltos-settings |
| PASS | boot splash (VeltOS Plymouth theme) is in the live initramfs | 1 |
| PASS | live welcome window started | 1523 |
| PASS | session uses VeltOS application names (XDG_DATA_DIRS) | XDG_DATA_DIRS=/var/lib/veltos/xdg:/usr/local/share:/usr/share |
| PASS | File Explorer and Control Panel names | Name=File Explorer; Name=Control Panel; Name=Global Theme; Name=Users; Name=Screen Locking; Name=Power Management; Name=Display Configuration; |
| PASS | per-user defaults: VeltOS style, File Explorer side bar, no live screen lock | [General]; theme=VeltOS; 1; Autolock=false; |
| PASS | booted via UEFI | efi |
| PASS | no crashed processes | none |

## Measurements

- **guest_agent_ready_s**: 14.1
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
```

### key_packages

```
linux-image-amd64 6.12.113-1
plasma-workspace 4:6.3.6-2
veltos-base 0.1.0~dev1
veltos-desktop 0.1.0~dev1
```

- **plasmashell_running_s**: 19.1
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
[    5.349966] veltos adduser[833]: The group `powerdev' does not exist.
[    5.379198] veltos adduser[835]: The group `scanner' does not exist.
[    5.459755] veltos adduser[844]: The group `debian-tor' does not exist.
[   14.057126] veltos obexd[1753]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
[   14.057929] veltos obexd[1753]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
```

- **systemd_analyze**: Startup finished in 2.963s (kernel) + 4.920s (userspace) = 7.883s
### free_m

```
               total        used        free      shared  buff/cache   available
Mem:            3915        1692         967         204        1686        2222
Swap:              0           0           0
```

- **idle_used_mib(MemTotal-MemAvailable)**: 1691
- **shmem_mib(live overlay tmpfs etc.)**: 204
### top_processes_by_rss

```
  651.0 MiB  plasmashell
  353.7 MiB  kwin_wayland
  253.8 MiB  DiscoverNotifie
  159.3 MiB  kded6
  151.2 MiB  xwaylandvideobr
  148.2 MiB  kdeconnectd
  141.5 MiB  polkit-kde-auth
  140.7 MiB  xdg-desktop-por
  133.3 MiB  kaccess
  121.1 MiB  ksmserver
   80.5 MiB  Xwayland
   56.9 MiB  org_kde_powerde
   46.3 MiB  startplasma-way
   43.7 MiB  packagekitd
   41.9 MiB  kactivitymanage
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
