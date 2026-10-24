# Faster app starts (2026-10-25, dev VM)

Item 15 of the product owner's 2026-10-23 list. Measured with
`starttime.py` (this folder: runs an app's launcher with Qt's QML loader
patched to report the first drawn frame) inside the live user's systemd
manager in the QEMU dev VM (KVM, 4 vCPUs, Mesa llvmpipe).

QML compiled at every start (before) and from VeltOS' content-keyed QML
cache (after, second and later starts):

| App | QML load before | QML load after | First frame after |
|---|---|---|---|
| Settings | 0.11-0.13 s | 0.08-0.09 s | 0.35-0.38 s |
| File Explorer | 0.08-0.14 s | 0.06 s | 0.33-0.37 s |
| Calendar | 0.11 s | 0.08 s | 0.35 s |
| Clock | 0.13 s | 0.05 s | 0.30-0.38 s |
| Mail | 0.35 s | 0.18 s | 0.61 s (from 0.82 s) |

The same with the CPU limited to 25 % (`systemd-run -p CPUQuota=25%`,
standing in for a slow PC or a VirtualBox VM): Settings 2.22 s → 1.80 s
to the first frame (QML 0.59 → 0.39 s), File Explorer QML 0.39 → 0.21 s.
The rest is Python and PySide6 importing (about 0.2 s at full speed) and
the first frame drawn by llvmpipe.

From a click in Start the taskbar shows the starting app's button at once
(it was already so; `taskbar-while-mail-starts.png`, frames while Mail started).
