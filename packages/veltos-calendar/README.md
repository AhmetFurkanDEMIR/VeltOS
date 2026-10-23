# veltos-calendar

VeltOS Calendar: the layout of Windows 11's Calendar app (product owner,
2026-10-22: "write a Calendar app, exactly like Windows 11's"), in English
and Turkish. PySide6 + QML, like the other VeltOS apps.

## What it does

- **Views**: day, work week, week, month and year, with "Today" and the
  previous / next arrows; a small month calendar and "New event" on the
  left. The small calendar's two-letter weekday names are the taskbar
  clock's ("Pt Sa Ça Pe Cu Ct Pa" in Turkish; Qt's abbreviations cut to
  two letters showed "Pz" for Monday, which reads as Sunday).
- **New event**: clicking a free time or a day opens Windows' quick card
  (name, date and time, all day, place, reminder); "More details" opens the
  full editor (repeat daily / weekly / monthly / yearly, reminder,
  description). An event opens its card with Edit and Delete.
- **Reminders**: VeltOS Clock's background agent (`veltos-clock-agent`)
  shows them as notifications while Calendar is closed
  (`store.due_reminders`; veltos-clock is recommended).
- **Storage**: one iCalendar file, `~/.local/share/veltos-calendar/calendar.ics`,
  that other calendar programs can import (`store.py`: folding, escaping,
  all-day events, `RRULE`, `VALARM` triggers; UTC times in other
  programs' files become local time). The window reloads when the file
  changes and moves "today" at midnight.
- Accent colour, dark mode and text size follow VeltOS Settings
  (kdeglobals).
- `veltos-calendar new-event` (the Start entry's "New event" action) opens
  with a new event; `veltos-calendar day|workweek|week|month|year` opens
  that view. The app icon is drawn by veltos-fluent-icons'
  `tools/app-icons.py` (the same drawing is in the Fluent icon theme and,
  as `data/veltos-calendar.svg`, in hicolor).

## Limits

- One calendar on this PC: no accounts or online calendars.
- Repeats have no end date and an event has one reminder; changing one
  occurrence of a repeating event changes the whole series.
- VeltOS writes only the parts of iCalendar it uses: lines it does not
  know in an imported file are dropped when it saves.

## Layout

| Path | Installed to |
|---|---|
| `veltos_calendar/` (`app.py`, `store.py`, `strings.py`, `qml/`) | `/usr/lib/python3/dist-packages/` |
| `bin/veltos-calendar` | `/usr/bin/` |
| `data/veltos-calendar.desktop` (action "New event") | `/usr/share/applications/` |
| `data/veltos-calendar.svg` (VeltOS artwork) | `/usr/share/icons/hicolor/scalable/apps/` |

## Tests

`tests/test_calendar.py` (package build): the iCalendar round trip,
reading other programs' files, saving and loading, repeating events,
reminders due in a time window and the next reminder, complete texts in
both languages, and the window (offscreen) in English and Turkish: every
view, a new event saved and deleted, moving an occurrence, navigation,
Turkish day and month names (weeks start on Monday).
