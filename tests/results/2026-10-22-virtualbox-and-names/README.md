# 2026-10-22 — VirtualBox black-screen fix, Office renamed

Taken in a throw-away VirtualBox VM on the developer host with the product
owner's settings (BIOS, VMSVGA, 16 MB video memory, 3D off; the owner's
own VMs untouched), cold-booting ISO
`veltos-0.1.0-dev-20261022-072126` with no manual steps.

| File | What it shows |
|---|---|
| `virtualbox-16mb-desktop.png` | The full VeltOS desktop (wallpaper, taskbar, Welcome window) painted on the owner's 16 MB VMSVGA VM, where every earlier ISO stayed black. The fix renders the Plasma/Qt stack in software when VirtualBox is detected (KWIN_COMPOSE=Q, QT_QUICK_BACKEND=software, LIBGL_ALWAYS_SOFTWARE=1). Superseded the same day: llvmpipe alone is right, the other two caused grey label boxes and a black Task View — see `../2026-10-22-virtualbox-renderer/`. |
| `start-menu-word-excel-powerpoint.png` | Start with the apps renamed to Word, Excel and PowerPoint and the Office icons (Word blue W, Excel green X, PowerPoint orange P). |

The QEMU boot test of the same ISO passed 18/18 on UEFI
(`out/test-results/20261022-073802-uefi`).
