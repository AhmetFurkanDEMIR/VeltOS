# Lock screen: Windows 11's sign-in sequence (2026-10-25, dev VM)

Item 24 of the product owner's 2026-10-23 list. QEMU dev VM, live system of
the 2026-10-23 ISO with this change's `veltos-desktop` installed (`dpkg
-i`), a password set for the live user, the session locked with `loginctl
lock-session`.

| Picture | What it shows |
|---|---|
| `1-lock-screen.png` | The lock screen: the picture with the time and date |
| `2-curtain-lifting.png` | A click, at normal speed (420 ms): the picture with the time goes up like a curtain, the blurred sign-in background shows under it |
| `2c-curtain-almost-gone-slowed.png` | The same with the animation slowed down six times in the VM's copy only (screenshots take about 0.3 s): the curtain uncovers the account picture, name and password box |
| `3-sign-in.png` | The sign-in view |
| `4-welcome.png` | After the right password: "Welcome" with Windows' five turning dots, 1.3 s before the desktop |
| `5-desktop.png` | Unlocked |
| `6-before-wake.png`, `7-after-wake.png` | The sign-in view left open, then the clock moved on two minutes (what the lock screen sees after the PC slept): it is back at the time, coming up from black |

Real sleep could not be shown in QEMU: after `systemctl suspend` and QMP
`system_wakeup` the virtio GPU stayed black and the session did not
recover (the VM had to be restarted). The lock screen tells a wake-up by
the clock jumping more than 20 seconds between two of its one-second ticks
(its timers stand still while the PC sleeps); the clock jump test above
exercises exactly that path. Not tested on real hardware.

Found while testing: after going back to the time, a key no longer lifted
the curtain (the hidden password box kept the keyboard focus), and the
sign-in box was drawn over the curtain while it was still lifting; both
fixed. Esc turns the screen off: kscreenlocker does that itself on every
Esc release (greeterapp.cpp, Plasma 6.3) and keeps the key from the QML,
so it stays; Windows only lowers the curtain.
