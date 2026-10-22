# 2026-10-22 — Session start: the portal platform theme (+75 s since the 2026-10-21 evening)

"It used to come at once." The QEMU boot tests, "plasmashell running for
live user":

| Test run (ISO) | plasmashell after |
|---|---|
| 20261021-165735 (the last ISO before the evening's) | 17.3 s |
| 20261021-233325 (the first with the portal file dialogs) | 96.1 s |
| 20261022-073802 | 95.5 s |
| 20261022-091502 (ISO 084833, UEFI) | 91.9 s |
| 20261022-091855 (ISO 084833, BIOS) | 96.9 s |

The kernel boot is unchanged (guest agent reachable after 12–14 s in all
of them); the difference is inside the session start.

| File | What it shows |
|---|---|
| `blame-before.png` | `systemd-analyze --user blame` in a throw-away VirtualBox VM (ISO 084833, 3D off): kcminit 54 s, ksplash 40 s, plasmashell 27 s, kactivitymanagerd / kded6 / ksmserver 25 s each — the D-Bus timeout, one per Qt service that asked the portal (`QT_QPA_PLATFORMTHEME=xdgdesktopportal`, set for the whole session since commit e676c2c) before the portal could be up. |
| `timeouts-before.png` | The journal: ksplash and `xdg-desktop-portal.service` timing out, `Failed to create settings proxy: Error calling StartServiceByName for org.freedesktop.impl.portal.desktop.kde` (the portal's own backend is a Qt program with the same theme), D-Bus activation of `org.freedesktop.portal.Desktop` timing out. |
| `after-units-state.png` | After a drop-in `Environment=QT_QPA_PLATFORMTHEME=kde` for every `plasma-*.service` and a session restart in the same VM: plasmashell runs with KDE's theme, the portal is active, ksplash finished normally; the desktop painted **15 s** after the restart (120–150 s before, same VM, same ISO). |

Ruled out in the same VM: the Wayland greeter of the same commit (restart
with it 150 s, with an X11 greeter 135 s) and VeltOS' own portal backend
(GLib, no Qt; run without the theme, 120 s and the portal still timed out).
