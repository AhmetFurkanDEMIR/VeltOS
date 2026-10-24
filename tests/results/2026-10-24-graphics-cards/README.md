# VeltOS Graphics Cards (2026-10-24, dev VM)

Item 9 of the product owner's 2026-10-23 list. QEMU dev VM (live system,
Turkish), packages built by `build/run.sh packages veltos-graphics
veltos-settings veltos-fluent-icons` and installed with `dpkg -i`.

| Picture | What it shows |
|---|---|
| `start-search-ekran-kartlari.png` | Start search finds "Ekran Kartları" with its icon |
| `virtio-gpu-properties-tr.png` | The VM's own card (virtio GPU): "no driver needs to be installed", properties (renderer llvmpipe, Mesa 25.0.7, Vulkan) |
| `amd-card-recorded-ready.png` | A recorded AMD RX 6600 `lspci` entry (`out/vm/gfx-fake.py`, everything else real): driver complete, "Check for updates" |
| `amd-check-for-updates-up-to-date.png` | After "Check for updates": real `pkcon refresh`, `apt-cache policy` found no newer firmware/Mesa: "The driver is up to date" |
| `nvidia-card-recorded-install-driver.png` | A recorded RTX 4060 on Nouveau: "Install driver" |
| `nvidia-installing-progress.png` | The real installation running (pkcon's percentage) |
| `nvidia-installed-restart-properties.png` | After it: "Restart now", properties with `nvidia-driver 550.163.01-2`, Secure Boot off, "Use the open-source driver" |
| `nvidia-removing.png` | "Use the open-source driver" removing NVIDIA's packages |
| `settings-display-graphics-cards-row.png` | Settings > System > Display > Related settings > Graphics cards (opens the app) |
| `app-icon-256.png` | The app icon (VeltOS artwork, `tools/app-icons.py`) |

Observed in the VM with the recorded NVIDIA card (the VM has no NVIDIA
GPU, so the driver could not load): `nvidia-detect` was installed, then
`nvidia-driver` and `linux-headers-amd64` from Debian non-free; DKMS built
`nvidia-current/550.163.01` for 6.12.113+deb13-amd64 and created
`/var/lib/dkms/mok.key`/`mok.pub`. Removing first hung (pkcon asked which
of the amd64/i386 `nvidia-driver-libs` was meant) and then left 37
packages; both fixed (names with the architecture, the whole NVIDIA
package set by name), after which only `nvidia-detect` stayed.

Not tested: a real NVIDIA/AMD/Intel GPU, Secure Boot key registration
(`mokutil --import`; the VM has no Secure Boot), a real driver update
(no newer package was available).
