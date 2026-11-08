# Items 170-176: Start's view switch, the stopwatch, crash checks, speed

Dev VM (QEMU/KVM, no 3D: KWin and the apps render with llvmpipe, as
VirtualBox without 3D acceleration does), installed system, user jordanl,
1920x1080, 2026-11-08. The scripts here are the dev aids that drove the
VM from the host (`build/run.sh vm ...`); they are copies of `out/vm/`.

## Start: switching the "All" view (item 170)

The product owner's Start crashed switching from List to Category. Not
reproduced in the VM, through the View menu (also with the list scrolled
and after a context menu) or with `start-view-stress.sh` (60 switches with
Start open) at 14 screen sizes and scales (`start-view-matrix.sh`:
1920x1080 at 100/125/150 %, 1360x768, 1280x768, 1280x960, 1024x768,
1440x900, 1680x1050 at 125 %, 2048x1152 at 150 %, 1280x1024 at 125 %,
1920x1200 at 125 %, 1440x900 and 1360x768 at 125 %): plasmashell kept its
process every time. Two causes were closed in the code: the switch now
happens after the View menu has closed (`Qt.callLater`), and Plasma's
ScrollView, which gave the scroll bar room only while the bar showed,
keeps it always, so the category cards (whose size follows the width)
can no longer make the bar come and go (the loop AGENTS.md describes for
Settings). `start-list-to-category.png`: the switch with the list
scrolled.

## Crash checks (item 172)

- `app-exit-1.log`: 21 VeltOS apps started in the session, still running
  after 9 s, closed with Alt+F4, no core dump (VeltOS AI stays by design
  and quits when idle).
- Eight apps open through four light/dark switches: all alive, no core
  dump.
- Signing out: no core dump. plasmashell restarted with `systemctl --user
  restart` while KWin runs dumps core on its way out (KWindowShadow after
  the Wayland connection is gone, KF6): only the dev aid does that.
- plasmashell killed with SIGSEGV: systemd started it again
  (`Restart=on-failure`), taskbar and desktop back within seconds.

## Speed (item 173)

`perf-scenes.sh`, CPU of one core over the scene, before and after:

| Scene | KWin before | KWin after |
|---|---|---|
| idle desktop | 0.0 % | 0.0 % |
| Start opened and closed 6 times (20 s) | 93.0 % | 55.9 % |
| Start left open (15 s, incl. opening) | 18.1 % | 10.1 % |
| Start open after the caret stopped (10 s) | 18 % (same as above) | 0.0 % |
| search window, typing (15 s) | 27.8 % | 25.6 % |
| Quick Settings opened and closed 4 times (15 s) | 37.2 % | 22.1 % |

KWin's own "Fading Popups" effect without any fade measured 37 % for the
Start scene; KWin's fade-out of 600 ms (OutQuart, nearly invisible after
about 250 ms) was the difference. `start-caret-steady.png`: the caret
after five seconds.

## Start's and search's context menus (item 174)

`start-app-menu.png`, `search-app-menu.png`: Plasma's entries that did
nothing on VeltOS are gone; "Pin to taskbar" pinned and unpinned
Calculator (the taskbar's launcher list changed at once); "Create shortcut
on desktop" made `veltos-calculator - Shortcut.desktop`.

## Task Manager (item 175)

`task-manager-names-before.png`: Settings listed as "Add a device" and
VeltOS Store as "App Installer" among the background processes, the bug
fixed by item 175.
