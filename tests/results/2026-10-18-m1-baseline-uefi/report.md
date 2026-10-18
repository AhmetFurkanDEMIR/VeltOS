# VeltOS boot test — uefi — PASS

- **iso**: veltos-0.1.0-dev-amd64.hybrid.iso
- **iso_sha256**: e72f66dcbc69ecaba7c8a5b7c3160b9d37359a0d0c19f372258b0ad6612065a7
- **firmware**: uefi
- **vm**: QEMU/KVM q35, 4 vCPU (host CPU model), 4096 MiB RAM, virtio-vga 1920x1080 (no 3D acceleration), virtio-net
- **qemu**: QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)
- **started_utc**: 20261018-210255
- **duration_s**: 91.3

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | guest agent reachable (system booted) | after 16.5s |
| PASS | os-release identifies VeltOS | PRETTY_NAME="VeltOS 0.1 (pre-alpha)"; NAME="VeltOS"; VERSION_ID="0.1"; VERSION="0.1 (pre-alpha)"; VERSION_CODENAME=trixie; ID=veltos; ID_LIKE=debian; ANSI_COLOR="38;2;79;124;255"; LOGO=veltos-logo; |
| PASS | VeltOS packages installed | linux-image-amd64 6.12.113-1 plasma-workspace 4:6.3.6-2 veltos-base 0.1.0~dev1 veltos-desktop 0.1.0~dev1 |
| PASS | plasmashell running for live user | after 25.1s |
| PASS | graphical session is Wayland | Name=velt; Type=wayland; State=active; Name=velt; Type=unspecified; State=active; |
| PASS | no failed systemd units | running |
| PASS | VeltOS taskbar layout applied | 2 panel spacers, icon tasks, VeltOS launcher icon |
| PASS | VeltOS wallpaper set |  |
| PASS | taskbar launcher .desktop files exist | ok org.kde.dolphin ok firefox-esr ok org.kde.konsole ok systemsettings |
| PASS | booted via UEFI | efi |

## Measurements

- **guest_agent_ready_s**: 16.5
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

- **plasmashell_running_s**: 25.1
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
[    4.897582] veltos adduser[817]: The group `powerdev' does not exist.
[    4.927286] veltos adduser[819]: The group `scanner' does not exist.
[    5.020246] veltos adduser[828]: The group `debian-tor' does not exist.
[   17.749003] veltos obexd[1772]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
[   17.750571] veltos obexd[1772]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
```

- **systemd_analyze**: Startup finished in 2.545s (kernel) + 4.532s (userspace) = 7.078s
### free_m

```
               total        used        free      shared  buff/cache   available
Mem:            3915        1696         436         194        2207        2219
Swap:              0           0           0
```

- **idle_used_mib(MemTotal-MemAvailable)**: 1696
- **shmem_mib(live overlay tmpfs etc.)**: 194
### top_processes_by_rss

```
  571.2 MiB  plasmashell
  332.5 MiB  plasma-welcome
  294.8 MiB  kwin_wayland
  241.2 MiB  DiscoverNotifie
  149.2 MiB  kded6
  148.0 MiB  xwaylandvideobr
  144.6 MiB  kdeconnectd
  129.5 MiB  polkit-kde-auth
  129.2 MiB  xdg-desktop-por
  121.6 MiB  kaccess
  121.2 MiB  ksmserver
   80.6 MiB  Xwayland
   56.1 MiB  org_kde_powerde
   46.1 MiB  startplasma-way
   41.7 MiB  kactivitymanage
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
- desktop: `02-desktop.png`
