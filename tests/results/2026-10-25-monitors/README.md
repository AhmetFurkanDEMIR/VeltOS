# Several monitors: picture, Windows + P, Settings > Display (2026-10-25, dev VM)

Item 23 of the product owner's 2026-10-23 list. QEMU dev VM (live system of
the 2026-10-23 ISO with this change's `veltos-settings` and `veltos-desktop`
installed by `dpkg -i`), started with `VELTOS_VM_OUTPUTS=2`: a virtio GPU
with two outputs, Virtual-1 (1920x1080) and Virtual-2 (preferred 1024x768),
the second one plugged in and out from inside the guest (DRM connector
forced on/off plus a hotplug uevent, see `docs/dev/testing.md`). Real
monitors, laptops and projectors were not tested.

| Picture | What it shows |
|---|---|
| `before-winp-kscreen.png` | Before: Windows + P opened KDE's display switcher (KScreen's OSD) |
| `winp-flyout.png` | Windows + P now: VeltOS' Project flyout at the bottom right, "Extend" current |
| `winp-flyout-tr.png` | The flyout in Turkish (Yansıt: Yalnızca bilgisayar ekranı, Çoğalt, Genişlet, Yalnızca ikinci ekran) |
| `duplicate-screen2.png` | Duplicate: the second screen shows screen 1's picture, both at 1024x768 |
| `settings-two-displays.png` | Settings > System > Display: the two displays to scale, Identify, Multiple displays, main display, scale, resolution, orientation |
| `settings-display2-selected.png` | Display 2 chosen in the arrangement: its own resolution (1024 x 768, Recommended) |
| `identify-screen1.png`, `identify-screen2.png` | Identify: each screen shows its number at the bottom left, above the taskbar |
| `main-display-screen2.png` | "Make this my main display" on display 2: the taskbar and desktop icons moved there |
| `settings-second-screen-only.png` | After Windows + P > Second screen only, on screen 2: "Show only on 2", display 1 dimmed, "This display is not in use" |
| `settings-follows-winp-extend.png` | Windows + P > Extend while Settings is open: the page changed to "Extend these displays" by itself |
| `unplugged.png` | Screen 2 unplugged: the Settings window came over to screen 1, the page shows one display |
| `replugged-screen2.png` | Plugged in again: screen 2 is extended again and the window went back to it |

Found and fixed while testing (unit tests added for each):

- KScreen's kded module (applies saved layouts, reacts to new monitors) was
  not running in the VeltOS session although it autoloads; the session
  fix-up loads it (`qdbus6 org.kde.kded6 /kded loadedModules` lists
  `kscreen` now).
- KScreen kept Windows + P: a "none" for its shortcut in
  `/etc/xdg/kglobalshortcutsrc` was ignored; its `kglobalaccel` file is now
  hidden like Spectacle's (`update-app-names`), and kglobalaccel gives
  Meta+P and the Display key to VeltOS Settings' Project action.
- Duplicate chose 4096x2160 for both screens (the largest mode both list);
  it now takes the largest shared mode within every screen's preferred size
  (1024x768 here), and leaving Duplicate gives each screen its preferred
  mode back.
- Display numbers followed the main display, so "Make this my main display"
  renumbered the screens; numbers are fixed now (a laptop's screen 1, then
  KScreen's order).
- From one-screen-only back to Extend, the screen that had been alone stayed
  the main one; display 1 is main again (Windows does the same).

Checked with `kscreen-doctor -o` after each choice: Extend 0,0 1920x1080 and
1920,0 1024x768; Duplicate both 0,0 1024x768; PC screen only: Virtual-2
disabled; Second screen only: Virtual-1 disabled, Virtual-2 priority 1.
