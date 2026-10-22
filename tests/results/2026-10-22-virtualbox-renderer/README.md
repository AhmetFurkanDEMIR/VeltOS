# 2026-10-22 — VirtualBox renderer: llvmpipe alone

The product owner, testing ISO `veltos-0.1.0-dev-20261022-072126` in
VirtualBox, reported three things: the desktop takes long to appear, grey
boxes under the desktop icons' labels, and Task View showing "Desktop 1"
black. All three came from that ISO's VirtualBox fix being too blunt
(`KWIN_COMPOSE=Q` + `QT_QUICK_BACKEND=software` + `LIBGL_ALWAYS_SOFTWARE=1`).
Throw-away VirtualBox VMs on the developer host with the owner's settings
(BIOS, VMSVGA, 16 MB, 3D off), the session script edited in the VM and the
session restarted; the owner's own VMs untouched.

| File | What it shows |
|---|---|
| `before-all-software-desktop.png` | That ISO's session (all three variables): grey boxes under every desktop label. |
| `before-qpainter-taskview.png` | Task View under KWin's QPainter compositor: it opens, but the "Desktop 1" preview is black. |
| `after-llvmpipe-desktop.png` | `LIBGL_ALWAYS_SOFTWARE=1` alone (Mesa llvmpipe, KWin's OpenGL scene in software): plain labels with shadows, no boxes. Painted ~105 s after the session restart, measured while another VM was booting on the host. |
| `after-llvmpipe-taskview.png` | Task View with llvmpipe: the live window and a real "Desktop 1" preview. |
| `probe-3d-on-svga3d.png` | `eglinfo -B` in a VM with 3D acceleration on: Mesa's GBM renderer is "SVGA3D" (real OpenGL through the svga driver) — nothing must be forced there. |
| `probe-3d-off-llvmpipe.png` | The same with 3D off: the renderer is already "llvmpipe" — the only guest-visible difference (sysfs and DMI are identical), and now the rule in `needs-software-rendering`. |

Two earlier attempts of this test were void: a `99-*.sh` file in
`plasma-workspace/env` is sourced *before* `veltos-session.sh` and cannot
unset what it exports (AGENTS.md gotcha).
