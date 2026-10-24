# veltos-taskmanager

VeltOS Task Manager: the Windows 11 Task Manager layout on VeltOS
(PySide6 + QML, the VeltOS Settings palette). Opened with **Ctrl+Shift+Esc**
(`X-KDE-Shortcuts` in the desktop file) or from Start ("Task Manager").
KDE's detailed system monitor stays installed as "Resource Monitor".

## Pages

- **Processes**: Apps, Background processes and System processes, like
  Windows. An app is the topmost process of a visible application (matched
  by the program its `.desktop` file starts, or `StartupWMClass`) with its
  child processes; CPU (share of all CPUs), memory and GPU are their sums. Busy
  cells are tinted from pale to amber. Search box, "End task" (button,
  Delete key, context menu: SIGTERM, then SIGKILL after 3 s), "Run new
  task" (KRunner). Kernel threads are not listed. The list is updated in
  place every second (`model.py`), so scrolling, hover and selection stay.
- **Performance**: CPU, Memory, Disk, Network and every GPU ("GPU 0" ...)
  with small graphs; the selected one with a 60-second graph and figures
  (utilisation, speed, processes, up time, cores; memory in
  use/available; disk read/write; network send/receive; a GPU's busiest
  engine, its 3D/video engines, dedicated and shared memory, temperature,
  driver, location).
- **GPU figures** (`gpu.py`, no administrator rights): the kernel's DRM
  fdinfo of the user's processes (busy time per engine, per GPU and per
  process: Intel i915/xe, AMD and others), amdgpu's sysfs counters and
  memory, nvidia-smi for NVIDIA's driver. Drivers that publish nothing
  (nouveau, virtual machines) show "Not available" and an empty GPU
  column.
- **Startup apps**: freedesktop autostart entries (not session internals,
  i.e. `NoDisplay=true`, or entries for other desktops) with Enable/Disable;
  disabling writes `~/.config/autostart/<name>` with `Hidden=true`.

## Layout

| Path | What |
|---|---|
| `veltos_taskmanager/system.py` | psutil data, grouping, End task, performance samples, autostart |
| `veltos_taskmanager/gpu.py` | GPU utilization, memory and temperature; per-process GPU shares |
| `veltos_taskmanager/app.py` | `Backend` (Qt properties/slots), `main()` |
| `veltos_taskmanager/model.py` | Process rows model updated in place |
| `veltos_taskmanager/strings.py` | English/Turkish texts |
| `veltos_taskmanager/qml/` | `Main.qml`, pages, `Graph.qml`, `Theme.qml` |
| `data/` | Desktop file (Ctrl+Shift+Esc), app icon (VeltOS artwork) |
| `tests/` | Grouping, End task, performance rates, autostart with a fake psutil; the window offscreen in English and Turkish (Turkish C locale) |

## Limits

- Disk activity is the busy time of all disks together; GPU, per-process
  disk and network use, "App history", "Users", "Details" and "Services"
  pages are not there yet.
- System processes run as other users; ending them needs administrator
  rights and fails silently for now.

## "is not responding" window (2026-10-24)

When a window does not answer and the user closes it (Alt+F4, the
taskbar), KWin runs its helper `kwin_killer_helper`. veltos-taskmanager
diverts it (KDE's helper stays at `kwin_killer_helper.kde`) to
`/usr/libexec/veltos-taskmanager/not-responding`
(`veltos_taskmanager/notresponding.py`, `qml/NotResponding.qml`): the
program's icon with a warning badge, "<App> is not responding" (or
"“<window>” in <App> is not responding"), "If you close the program, you
might lose information you haven't saved.", and "Close the program"
(accent) / "Wait for the program to respond" as equal buttons in a grey
bar, English and Turkish, light and dark. The window carries the
program's desktop file name, so it shows the program's icon and sits next
to it on the taskbar. "Close the program" ends it as KWin's helper does:
a note for DrKonqi (`~/.cache/drkonqi/application-not-responding/`),
SIGABRT, and SIGKILL after 4 s; programs of other users and other hosts
go to KDE's helper, which can ask for permission. Esc and the window's
Close button wait. Tests: `tests/test_notresponding.py` (KWin's options,
name and icon from the desktop file, the caption without the program's
name, ending order, the DrKonqi note, other hosts, the window offscreen in
English and Turkish). Seen in the dev VM: Notepad stopped with SIGSTOP,
Alt+F4 → this window; "Close the program" ended it, "Wait" left it
(`tests/results/2026-10-24-not-responding/`).

## Notice after a crash (2026-10-25)

`crash.py` (`/usr/libexec/veltos-taskmanager/crash-notice`) replaces the
program of DrKonqi's per-crash user service
(`drkonqi-coredump-launcher@.service.d/veltos-crash-notice.conf`): systemd
hands it the crash record (JSON from DrKonqi's system service); for an
app (found from the unit Plasma started it in, or from the program) it
shows one toast like Windows 11's, with the app's name and icon, "<App>
closed unexpectedly" and "Restart" (KIO starts the app again). Background
services crash silently. DrKonqi's window, "Report Bug" and tray icon are
not used; its sign-in pick-up of earlier crashes is off
(`drkonqi-coredump-pickup.service.d`).
