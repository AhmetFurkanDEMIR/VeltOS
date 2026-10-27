# veltos-graphics — VeltOS Graphics Cards

The PC's graphics cards in one window, in the look of Windows 11
Settings (product owner, 2026-10-23: "find NVIDIA or AMD cards
automatically and install their driver completely and properly"). Start:
"Graphics Cards" / "Ekran Kartları"; VeltOS Settings > System > Display >
Graphics cards.

Each card shows its name, the driver it uses and an InfoBar with the one
button that completes its driver:

| Card | State | Button |
|---|---|---|
| NVIDIA without NVIDIA's driver | NVIDIA's driver is available | Install driver |
| NVIDIA, driver installed, not loaded yet | restart needed | Restart now |
| NVIDIA, driver installed, PC restarted, not loaded | why: Secure Boot key, not built for this kernel, or other | Repair (rebuilds with DKMS) / Details (driver log) |
| NVIDIA with NVIDIA's driver in use | complete | Check for updates; "Use the open-source driver" under Properties |
| NVIDIA that needs a legacy series (390/340/470) | Debian 13 has none: stays on Nouveau | — |
| AMD / Intel, firmware or Mesa missing | missing parts named | Install |
| AMD / Intel, complete | complete | Check for updates |
| Virtual machine (virtio, VMware, VirtualBox, QXL, Hyper-V) | nothing to install | — |

Properties: manufacturer, model, board, PCI ID, location, kernel driver,
modules, driver version, driver package, video memory (AMD: sysfs,
NVIDIA: nvidia-smi), and for the card the PC draws with (`boot_vga`) the
OpenGL renderer, OpenGL and Mesa versions and Vulkan devices.

## How it works

- `gpus.py`: `lspci -vmmnnk` (PCI class 03xx), sysfs, `eglinfo -B` (GBM
  platform: no window needed), `vulkaninfo --summary`. No administrator
  rights.
- `drivers.py`: the plan per card. Packages verified in Debian 13 on
  2026-10-24: `nvidia-driver` 550.163.01-2 and `nvidia-tesla-535-driver`
  (non-free, DKMS), `nvidia-detect` (says which one a card needs),
  `linux-headers-amd64` (DKMS builds against it), `firmware-amd-graphics`
  / `firmware-intel-graphics` 20250410-2 (non-free-firmware),
  `mesa-vulkan-drivers` / `libgl1-mesa-dri` 25.0.7-2+deb13u1. Installed
  systems have `main contrib non-free non-free-firmware` (Calamares'
  `sources-final`).
- `app.py`: installs with `pkcon -p install …` (PackageKit; polkit asks
  for the administrator's password through VeltOS' prompt). pkcon runs in
  a pseudo terminal that answers its "Proceed with changes?"
  (`ptyrun.py`, the same file as VeltOS Store's): `-y` made the
  transaction non-interactive and polkit refused without asking ("The
  driver could not be installed. Administrator permission was not
  given." on the product owner's laptop, 2026-10-26). First
  `pkcon refresh` when apt's lists are older than a day, and for NVIDIA
  `nvidia-detect` before choosing the package. Package names carry the
  architecture (`nvidia-driver:amd64`): VeltOS also has i386 (Wine), and
  pkcon otherwise asks which one is meant and waits. "Check for updates"
  refreshes, asks apt (`apt-cache policy`) which packages have a newer
  version and updates only those (`pkcon update NAME` fails when NAME has
  none). "Use the open-source driver" removes every package of NVIDIA's
  stack by name (`drivers.NVIDIA_STACK`, amd64 and i386; removing only
  `nvidia-driver` left 37). Reading the cards runs in a thread so the
  window opens at once.
- Secure Boot: DKMS signs NVIDIA's module with `/var/lib/dkms/mok.key`;
  when Secure Boot is on and the key is not enrolled, the card asks for a
  one-time password and runs `pkexec mokutil --import
  /var/lib/dkms/mok.pub`; the firmware's MOK manager asks for it at the
  next start.

- Monitors with NVIDIA's driver: Debian 13's NVIDIA modules (550,
  Tesla 535, the open 550 modules) leave the kernel's modesetting off
  (`nvidia-drm` `modeset` defaults to false, no Debian option turns it
  on; checked in the packages on 2026-10-27), and KWin on Wayland drives
  screens only through it: every monitor on the NVIDIA card disappeared
  once the driver replaced Nouveau (product owner's laptop).
  `/usr/lib/modprobe.d/veltos-nvidia.conf` sets `modeset=1` for Debian's
  module names (`nvidia-current-drm`, `nvidia-current-open-drm`,
  `nvidia-tesla-535-drm`); Debian loads `nvidia-drm` at start-up
  (`/etc/modules-load.d/nvidia.conf`).
- Kernel and headers: DKMS builds the module for kernels whose headers
  are installed. The install brings `linux-headers-amd64`,
  `linux-image-amd64` (so the newest kernel and its headers match) and the
  running kernel's headers. After a restart without NVIDIA's module the
  card says why: Secure Boot's key (register it), no module for this
  kernel ("Repair": the running kernel's headers, then `pkexec dkms
  autoinstall -k KERNEL`), or anything else (Details).
- Driver log (`diagnostics.py`, "Driver log" at the top, "Details" on a
  failure): the commands VeltOS ran with pkcon's and DKMS's output
  (`~/.local/state/veltos-graphics/driver.log`, last 512 KB), Secure Boot,
  loaded modules with `modeset`, the screens' DRM connectors, `dkms
  status`, DKMS's build log and dpkg's history of driver packages; "Add
  kernel messages" adds `journalctl -k` (pkexec asks for the password),
  Copy, and "Save and open" (Documents, opens in Notepad).

## Tests

`tests/` (run by the package build): recorded lspci/eglinfo/vulkaninfo/
nvidia-detect output (`samples.py`) for an Intel + NVIDIA laptop, an AMD
card, QEMU's virtio GPU and a legacy NVIDIA card; the real window
offscreen in English and Turkish with a stand-in for pkcon.

Not tested on real NVIDIA/AMD/Intel hardware (the modesetting fix
included) or with Secure Boot on: the
developer machine has none in a VM (see `docs/dev/status.md`).
