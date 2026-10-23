"""Events of VeltOS Calendar, kept as an iCalendar file (RFC 5545):

    ~/.local/share/veltos-calendar/calendar.ics

Other calendar programs read and import the same file. VeltOS writes the
part of the format it uses: events (VEVENT) with a title, a place, notes,
a start and an end (a local time, or whole days), a repetition (daily,
weekly, monthly or yearly, without end) and one reminder (VALARM, minutes
before). Lines it does not know in a file are dropped when it saves.
Standard library only.
"""

import datetime
import json
import os
import re
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPEATS = ("none", "daily", "weekly", "monthly", "yearly")
# Reminder choices, in minutes before the start, as Windows offers them
# (-1 = none; whole-day events count from 0:00).
REMINDERS = (-1, 0, 5, 15, 30, 60, 120, 720, 1440, 10080)
COLOURS = ("#2F5EE6", "#0F9D58", "#C42B1C", "#E3801B", "#8E44AD", "#00838F")


def data_dir():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "veltos-calendar"


def calendar_path():
    return data_dir() / "calendar.ics"


@dataclass
class Event:
    title: str
    start: datetime.datetime          # whole-day events: midnight of the first day
    end: datetime.datetime            # exclusive: midnight after the last day
    all_day: bool = False
    location: str = ""
    notes: str = ""
    repeat: str = "none"
    reminder: int = 15
    uid: str = field(default_factory=lambda: f"{uuid.uuid4()}@veltos")

    def duration(self):
        return self.end - self.start

    def to_dict(self):
        data = asdict(self)
        data["start"] = self.start.isoformat(timespec="minutes")
        data["end"] = self.end.isoformat(timespec="minutes")
        return data


# --- iCalendar text ----------------------------------------------------------------------

def escape(text):
    return (text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\\n").replace("\n", "\\n"))


def unescape(text):
    out, i = [], 0
    while i < len(text):
        char = text[i]
        if char == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            out.append("\n" if nxt in "nN" else nxt)
            i += 2
        else:
            out.append(char)
            i += 1
    return "".join(out)


def fold(line):
    """Lines longer than 75 octets continue on the next line after a space."""
    data = line.encode("utf-8")
    if len(data) <= 75:
        return line
    parts, current = [], b""
    for char in line:
        encoded = char.encode("utf-8")
        if len(current) + len(encoded) > (75 if not parts else 74):
            parts.append(current.decode("utf-8"))
            current = b""
        current += encoded
    parts.append(current.decode("utf-8"))
    return "\r\n ".join(parts)


def unfold(text):
    return re.sub(r"\r?\n[ \t]", "", text).splitlines()


def format_time(moment, all_day):
    if all_day:
        return f";VALUE=DATE:{moment:%Y%m%d}"
    return f":{moment:%Y%m%dT%H%M%S}"


def parse_time(params, value):
    """(datetime, whole day?) of a DTSTART/DTEND value; UTC times ("Z")
    are turned into local time."""
    value = value.strip()
    if "VALUE=DATE" in params.upper() or re.fullmatch(r"\d{8}", value):
        day = datetime.datetime.strptime(value[:8], "%Y%m%d")
        return day, True
    moment = datetime.datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
    if value.endswith("Z"):
        moment = moment.replace(tzinfo=datetime.timezone.utc).astimezone().replace(tzinfo=None)
    return moment, False


def to_ics(events):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//VeltOS//Calendar//EN", "CALSCALE:GREGORIAN"]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for event in events:
        lines += ["BEGIN:VEVENT", f"UID:{event.uid}", f"DTSTAMP:{stamp}",
                  "DTSTART" + format_time(event.start, event.all_day),
                  "DTEND" + format_time(event.end, event.all_day),
                  f"SUMMARY:{escape(event.title)}"]
        if event.location:
            lines.append(f"LOCATION:{escape(event.location)}")
        if event.notes:
            lines.append(f"DESCRIPTION:{escape(event.notes)}")
        if event.repeat in REPEATS[1:]:
            lines.append(f"RRULE:FREQ={event.repeat.upper()}")
        if event.reminder >= 0:
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{escape(event.title)}",
                      f"TRIGGER:-PT{event.reminder}M", "END:VALARM"]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in lines) + "\r\n"


def parse_trigger(value):
    """Minutes before the start of a TRIGGER like -PT15M, -P1D, -PT1H30M."""
    match = re.fullmatch(r"-P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", value.strip())
    if not match:
        return 0 if value.strip() in ("PT0S", "-PT0S", "PT0M") else -1
    weeks, days, hours, minutes, _seconds = (int(g) if g else 0 for g in match.groups())
    return ((weeks * 7 + days) * 24 + hours) * 60 + minutes


def from_ics(text):
    events, current, in_alarm = [], None, False
    for line in unfold(text):
        if ":" not in line:
            continue
        name_params, value = line.split(":", 1)
        name, _, params = name_params.partition(";")
        name = name.upper()
        if name == "BEGIN" and value.upper() == "VEVENT":
            current = {"reminder": -1}
        elif name == "END" and value.upper() == "VEVENT" and current is not None:
            if "start" in current:
                start, all_day = current["start"]
                end = current.get("end", (start + (datetime.timedelta(days=1) if all_day
                                                    else datetime.timedelta(hours=1)), all_day))[0]
                if end <= start:
                    end = start + (datetime.timedelta(days=1) if all_day else datetime.timedelta(minutes=30))
                events.append(Event(title=current.get("title", ""), start=start, end=end, all_day=all_day,
                                    location=current.get("location", ""), notes=current.get("notes", ""),
                                    repeat=current.get("repeat", "none"), reminder=current["reminder"],
                                    uid=current.get("uid") or f"{uuid.uuid4()}@veltos"))
            current = None
        elif current is None:
            continue
        elif name == "BEGIN" and value.upper() == "VALARM":
            in_alarm = True
        elif name == "END" and value.upper() == "VALARM":
            in_alarm = False
        elif in_alarm:
            if name == "TRIGGER" and current["reminder"] < 0:
                current["reminder"] = parse_trigger(value)
        elif name == "UID":
            current["uid"] = value.strip()
        elif name == "SUMMARY":
            current["title"] = unescape(value)
        elif name == "LOCATION":
            current["location"] = unescape(value)
        elif name == "DESCRIPTION":
            current["notes"] = unescape(value)
        elif name in ("DTSTART", "DTEND"):
            try:
                current["start" if name == "DTSTART" else "end"] = parse_time(params, value)
            except ValueError:
                pass
        elif name == "RRULE":
            match = re.search(r"FREQ=(DAILY|WEEKLY|MONTHLY|YEARLY)", value.upper())
            current["repeat"] = match.group(1).lower() if match else "none"
    return events


def load(path=None):
    path = Path(path or calendar_path())
    try:
        return from_ics(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []


def save(events, path=None):
    """Written next to the old file and moved over it, so a crash never
    leaves half a calendar."""
    path = Path(path or calendar_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".calendar-", suffix=".ics", dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
        handle.write(to_ics(events))
    os.replace(tmp, path)


# --- Occurrences and reminders -----------------------------------------------------------

def add_months(moment, months):
    """The same day `months` later, or None when that month has no such
    day (31 April): Windows skips such months as well."""
    month = moment.month - 1 + months
    year, month = moment.year + month // 12, month % 12 + 1
    try:
        return moment.replace(year=year, month=month)
    except ValueError:
        return None


def nth_start(event, n):
    if event.repeat == "daily":
        return event.start + datetime.timedelta(days=n)
    if event.repeat == "weekly":
        return event.start + datetime.timedelta(weeks=n)
    if event.repeat == "monthly":
        return add_months(event.start, n)
    if event.repeat == "yearly":
        return add_months(event.start, 12 * n)
    return event.start if n == 0 else None


def occurrences(events, range_start, range_end):
    """[(event, start, end)] of everything that touches [range_start,
    range_end), sorted by start; repeating events once per repetition."""
    found = []
    for event in events:
        length = event.duration()
        if event.repeat == "none":
            if event.start < range_end and event.end > range_start:
                found.append((event, event.start, event.end))
            continue
        # Jump close to the range first, then step.
        if event.repeat == "daily":
            first = max(0, (range_start - length - event.start).days)
        elif event.repeat == "weekly":
            first = max(0, (range_start - length - event.start).days // 7)
        elif event.repeat == "monthly":
            first = max(0, (range_start.year - event.start.year) * 12 + range_start.month - event.start.month - 2)
        else:
            first = max(0, range_start.year - event.start.year - 1)
        n = first
        while n < first + 4000:
            start = nth_start(event, n)
            n += 1
            if start is None:
                continue
            if start >= range_end:
                break
            if start + length > range_start:
                found.append((event, start, start + length))
    found.sort(key=lambda item: (item[1], not item[0].all_day, item[0].title.casefold()))
    return found


def reminder_time(event, start):
    if event.reminder < 0:
        return None
    return start - datetime.timedelta(minutes=event.reminder)


def due_reminders(events, since, until):
    """[(event, start)] whose reminder falls in (since, until]."""
    due = []
    horizon = until + datetime.timedelta(minutes=max([e.reminder for e in events] + [0]) + 1)
    for event, start, _end in occurrences(events, since - datetime.timedelta(days=1), horizon):
        moment = reminder_time(event, start)
        if moment is not None and since < moment <= until:
            due.append((event, start))
    return due


def next_reminder(events, after):
    """When the next reminder after `after` is due (None if none within a year)."""
    soonest = None
    for event, start, _end in occurrences(events, after, after + datetime.timedelta(days=366)):
        moment = reminder_time(event, start)
        if moment is not None and moment > after and (soonest is None or moment < soonest):
            soonest = moment
    return soonest


def event_from_dict(data):
    """An Event from the editor's fields (strings), or ValueError."""
    title = str(data.get("title", "")).strip()
    all_day = bool(data.get("allDay"))
    start = datetime.datetime.fromisoformat(str(data["start"]))
    end = datetime.datetime.fromisoformat(str(data["end"]))
    if all_day:
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end.replace(hour=0, minute=0, second=0, microsecond=0)
        if end <= start:
            end = start + datetime.timedelta(days=1)
    elif end <= start:
        end = start + datetime.timedelta(minutes=30)
    repeat = data.get("repeat", "none")
    reminder = int(data.get("reminder", 15))
    return Event(title=title, start=start, end=end, all_day=all_day,
                 location=str(data.get("location", "")).strip(), notes=str(data.get("notes", "")),
                 repeat=repeat if repeat in REPEATS else "none",
                 reminder=reminder if reminder in REMINDERS else 15,
                 uid=str(data.get("uid") or "") or f"{uuid.uuid4()}@veltos")


def dumps(event):
    return json.dumps(event.to_dict(), ensure_ascii=False)
