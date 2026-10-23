# veltos-recovery

VeltOS Automatic Repair: when VeltOS does not finish starting twice in a
row, the PC opens a repair screen by itself, like Windows 11's Automatic
Repair (product owner, 2026-10-22: restart automatically after a failed
start and then start a modern repair mode with a terminal).

## How a failed start is noticed

| Piece | What it does |
|---|---|
| GRUB (veltos-boot's `/etc/grub.d/10_linux`) | Every start of a VeltOS entry (not Debian's "(recovery mode)" entries or VeltOS Recovery itself) runs `veltos_count_start`: `veltos_failed` in `/boot/grub/grubenv` becomes 1, then 2. When it is 2, the default entry is **VeltOS Recovery**. Only where GRUB can write its environment (not Btrfs/ZFS, LVM, RAID or an encrypted `/boot`; Debian's recordfail has the same limit). |
| `veltos-boot-ok.service` | Wanted by `graphical.target`: when the sign-in screen (display manager) has been up for 10 s, `grub-editenv … unset veltos_failed`. |
| `panic=10` (veltos-boot's `veltos.cfg`) | A kernel panic, or an initramfs that cannot find the system disk, restarts the PC after 10 s instead of stopping. |
| `veltos-boot-failed.service` | Wanted by `emergency.target` and `rescue.target`, and `OnFailure=` of `sddm.service` (systemd gave up restarting the sign-in screen): shows a short message and restarts after 20 s. Only on normal starts (not `single`, `emergency`, `rescue`, a `systemd.unit=` for those, or the recovery start) and only in the first 5 minutes. |
| `journald.conf.d/veltos-recovery.conf` | Keeps the journal on disk (200 MB at most), so the repair screen can show the failed start's errors. |

## The repair screen

The **VeltOS Recovery** entry starts Linux with `nomodeset` and
`systemd.unit=veltos-recovery.target`: the system without the sign-in
screen, `veltos-recovery.service` on the first console and a text login on
the second. The window (`veltos_recovery/`, PySide6/QML) runs as root with
Qt's `linuxfb` platform and the software scene graph: no compositor and no
GPU driver are needed.

- **VeltOS couldn't start correctly** (after failed starts: `run-recovery`
  finds `veltos_failed=2` and passes `--automatic`), with Restart and
  Advanced options at the bottom right. Chosen by hand from the boot menu
  (`--manual`), the screen opens straight on Choose an option, like
  Windows' Troubleshoot; its first page is then titled **Automatic
  Repair**.
- **Choose an option**: Startup Repair, Safe mode, Command Prompt, Problem
  details, Continue, Turn off your PC, as tiles (keyboard and mouse).
- **Startup Repair** runs, step by step: `dpkg --configure -a`,
  `apt-get --no-download --fix-broken install` (no network needed), room
  on a nearly full disk (under 1 GiB free on `/`: `apt-get clean`,
  journal to 100 MB),
  `update-initramfs -u -k all`, `update-grub`, `systemctl reset-failed`.
  Failed steps show their output in a terminal-style box.
- **Safe mode** clears the counter and starts the **VeltOS (safe graphics)**
  entry once (`grub-reboot veltos-safe`, `nomodeset`): the desktop without
  a graphics driver, on the firmware's frame buffer. Debian's kernel has no
  simpledrm, so such a start has no DRM device and Wayland cannot run (the
  screen stayed black); `veltos-safe-graphics.service` (before the
  sign-in screen, after Plymouth) then writes
  `/etc/sddm.conf.d/zz-veltos-safe-graphics.conf` (`DisplayServer=x11`)
  and sets the console back to text mode (Plymouth's frame-buffer
  renderer leaves it in graphics mode, and Linux ignores the switch to
  SDDM's console then), removes the file at every start with a driver,
  and the VeltOS sign-in screen starts Plasma on X11 (Xorg's fbdev
  driver).
- **Command Prompt** closes the window (exit status 3: while Qt draws, the
  console is in graphics mode and Linux ignores switches to another
  console) and `run-recovery` opens a sign-in on the next free console
  with the system's console font (`setupcon`) and a hint above it: sign in
  with your account and use `sudo`; after `exit` (or the sign-in's 60 s
  timeout) the window comes back on Choose an option (`--options`).
- **Problem details**: the previous start's errors and failed units from
  the journal (`journalctl -b -1`).
- **Continue** and **Restart** clear the counter and restart; **Turn off**
  powers off.

Texts in English and Turkish, from the system's `LANG`
(`/etc/default/locale`).

## Limits

- The repair screen runs from the system disk: when that disk cannot be
  found at all, the recovery start (which has no `panic=10`) stops at the
  initramfs shell instead.
- Not on the live medium (its boot menu keeps no counter).
- The unit tests cover the logic, the unit files and the screen
  (offscreen). The chain ran in a QEMU VM (installed system, UEFI,
  2026-10-22): GRUB counted a start and `boot-ok` cleared it, a count of
  two started the repair screen (1024x768 frame buffer), Advanced
  options, Problem details, Startup Repair, Command Prompt (sign-in,
  `exit`, back on the options), Restart and Safe mode (the desktop on X11
  and the frame buffer, with the setting written by hand before the
  package had `safe-graphics`) worked. Not yet run: Turn off, a BIOS
  machine, real hardware; see `docs/status.md`.

## Installed files

`/usr/bin/veltos-recovery` and the Python package `veltos_recovery`; the
package's own copy of the logo, `/usr/share/veltos-recovery/veltos-logo.svg`
(the repair start does not depend on the desktop's icons, which may be
what is broken; `tests/repo` keeps it identical to the master logo);
`/usr/lib/veltos-recovery/{run-recovery,boot-ok,boot-failed,safe-graphics}`; in
`/usr/lib/systemd/system/` the units `veltos-recovery.target`,
`veltos-recovery.service`, `veltos-boot-ok.service`,
`veltos-boot-failed.service` and `veltos-safe-graphics.service` (pulled
in by the sddm drop-in), wired by static links
(`graphical.target.wants`, `emergency.target.wants`,
`rescue.target.wants`; the maintainer scripts enable and start nothing)
and the drop-in `sddm.service.d/veltos-recovery.conf`;
`/usr/lib/systemd/journald.conf.d/veltos-recovery.conf`;
`/usr/share/doc/veltos-recovery/README.md` (the units' `Documentation=`).
Texts use Inter; the terminal-style output box uses Cascadia Mono
(`fonts-cascadia-code`, Recommends).

## Tests

`tests/test_recovery.py` (package build): the counter and the restart/safe
mode/power commands, Startup Repair's steps and the room check, reading
the previous start's problems, the language, complete texts, the unit files
and scripts (conditions, `boot-ok` waits for the sign-in screen), the
window loading without QML warnings, and "Choose an option" fitting
1024x768 and 800x600 screens in two columns (offscreen).
