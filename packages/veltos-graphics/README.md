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
- `app.py`: installs with `pkcon -p -y install …` (PackageKit; polkit asks
  for the administrator's password through VeltOS' prompt), first
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

## Tests

`tests/` (run by the package build): recorded lspci/eglinfo/vulkaninfo/
nvidia-detect output (`samples.py`) for an Intel + NVIDIA laptop, an AMD
card, QEMU's virtio GPU and a legacy NVIDIA card; the real window
offscreen in English and Turkish with a stand-in for pkcon.

Not tested on real NVIDIA/AMD/Intel hardware or with Secure Boot on: the
developer machine has none in a VM (see `docs/dev/status.md`).
