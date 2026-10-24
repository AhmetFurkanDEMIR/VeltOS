# Num Lock on by default, the user's choice kept (2026-10-24, dev VM)

Item 12 of the product owner's 2026-10-23 list. QEMU dev VM (live system,
PS/2 keyboard `input0` with its LED class entries), veltos-desktop built
by `build/run.sh packages veltos-desktop` and installed with `dpkg -i`.

Observed (`/sys/class/leds/input0::numlock/brightness`, `~/.config/kcminputrc`):

| Step | Num Lock light | kcminputrc |
|---|---|---|
| New session (`systemctl restart sddm`), no user setting | 1 (on: `/etc/xdg/kcminputrc` NumLock=0) | no `[Keyboard]` |
| Num Lock key pressed (QMP `num_lock`) | 0 | — |
| `systemctl --user stop veltos-numlock.service` (what the end of a session does) | 0 | `[Keyboard] NumLock=1` |
| New session | 0 (off, as left) | `NumLock=1` |

`veltos-numlock.service` was `active` in the session; it is ordered after
`plasma-kwin_wayland.service`, so it stops (and saves) before KWin. A
sign-out through `org.kde.Shutdown.logout` from `systemd-run` did not end
the live session in the VM, so the save was triggered by stopping the
unit; a real sign-out/shut-down through Start was not observed.
