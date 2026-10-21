# veltos-clock — VeltOS Clock

Windows 11's Clock app for VeltOS: **Focus sessions**, **Timer**, **Alarm**,
**Stopwatch** and **World clock** in one window with a navigation pane,
in English and Turkish (PySide6/QML).

| Part | What |
|---|---|
| `veltos_clock/store.py` | `~/.config/veltos-clock/clock.json`: alarms (time, name, repeat days, snooze), timers (duration, running/paused state), world clocks, focus length; and the one place that decides when an alarm or timer is due (`next_ring`, `due_alarms`, `due_timers`), tested without a window. |
| `veltos_clock/app.py` + `qml/Main.qml` | The window: alarm cards with a toggle, timer cards with a progress ring and Start/Pause/Reset, the stopwatch with laps, world clock cards with the time and the difference to local time, focus sessions (quiet notifications for the chosen length). Dialogs for adding alarms (hour/minute steppers, repeat chips, snooze), timers and cities. |
| `veltos_clock/agent.py` (`veltos-clock-agent`) | Rings alarms and finished timers while the app is closed: a notification with Snooze/Dismiss and the VeltOS alarm sound (veltos-desktop's `alarm-clock-elapsed`), repeated until answered or after two minutes. GLib only, started with the session (`/etc/xdg/autostart`), ~15 MB. |

Verified by the package tests: when one-time and repeating alarms ring
(today/tomorrow, weekdays, no second ring at the same time, no late ring
after sleep, snooze), timers (start/pause/resume/reset/due), the file
format, and the window loaded offscreen in English and Turkish with
every page, an alarm, a running timer and a world clock.

Not yet: alarm sounds other than the VeltOS one, Windows' "Clock" live
tile of upcoming alarms on the lock screen.
