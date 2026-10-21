"""What VeltOS Clock keeps, and when alarms and timers are due.

Everything is one JSON file, ~/.config/veltos-clock/clock.json, shared by
the app and the alarm agent (agent.py), which rings alarms and timers
while the app is closed:

    alarms:  [{id, time "HH:MM", name, days [0..6] (Monday = 0; [] = once),
               enabled, snooze (minutes), fired "YYYY-MM-DDTHH:MM" (the
               last ring, so one ring per time), snoozed "...T..." (rings
               again then)}]
    timers:  [{id, seconds, name, state "idle"|"running"|"paused",
               end (epoch seconds while running), left (seconds while
               paused), rang (true once the end was announced)}]
    clocks:  [{zone "Europe/Istanbul"}]
    focus:   {minutes}

No times are computed in QML: `next_ring` and `due` are the one place,
tested without any window.
"""

import datetime
import json
import os
import uuid
from pathlib import Path

DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def data_path():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "veltos-clock" / "clock.json"


def empty():
    return {"alarms": [], "timers": [], "clocks": [], "focus": {"minutes": 30}}


def load(path=None):
    path = path or data_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty()
    if not isinstance(data, dict):
        return empty()
    result = empty()
    for key in ("alarms", "timers", "clocks"):
        if isinstance(data.get(key), list):
            result[key] = [item for item in data[key] if isinstance(item, dict)]
    if isinstance(data.get("focus"), dict):
        result["focus"].update(data["focus"])
    return result


def save(data, path=None):
    path = path or data_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    tmp.replace(path)


def new_id():
    return uuid.uuid4().hex[:12]


def parse_time(text):
    """"07:30" -> (7, 30); None when it is not a time."""
    try:
        hours, minutes = (int(p) for p in str(text).split(":")[:2])
    except ValueError:
        return None
    if 0 <= hours < 24 and 0 <= minutes < 60:
        return hours, minutes
    return None


def stamp(moment):
    return moment.strftime("%Y-%m-%dT%H:%M")


def next_ring(alarm, now):
    """When an enabled alarm rings next (a naive local datetime), or None.
    A snoozed alarm rings at its snooze time; a one-time alarm today if
    its time is still ahead, else tomorrow; a repeating alarm on the next
    of its days."""
    if not alarm.get("enabled", True):
        return None
    snoozed = alarm.get("snoozed")
    if snoozed:
        try:
            return datetime.datetime.strptime(snoozed, "%Y-%m-%dT%H:%M")
        except ValueError:
            pass
    parsed = parse_time(alarm.get("time", ""))
    if parsed is None:
        return None
    hours, minutes = parsed
    days = sorted({int(d) for d in alarm.get("days", []) if isinstance(d, int) and 0 <= d <= 6})
    fired = alarm.get("fired", "")
    for offset in range(0, 9):
        day = (now + datetime.timedelta(days=offset)).date()
        candidate = datetime.datetime.combine(day, datetime.time(hours, minutes))
        if days and day.weekday() not in days:
            continue
        if stamp(candidate) == fired:
            continue                        # already rang at this time
        if candidate < now - datetime.timedelta(minutes=1) and not (days or offset == 0):
            continue
        if candidate < now - datetime.timedelta(minutes=1):
            continue                        # this day's time has passed: the next day
        return candidate
    return None


def due_alarms(data, now, grace_minutes=5):
    """Alarms whose ring time has come (and no more than `grace_minutes`
    ago, so a PC that was asleep does not ring every missed alarm)."""
    result = []
    for alarm in data.get("alarms", []):
        when = next_ring(alarm, now)
        if when is None:
            continue
        if when <= now and now - when <= datetime.timedelta(minutes=grace_minutes):
            result.append((alarm, when))
    return result


def ring(alarm, when):
    """Record the ring: a one-time alarm switches off afterwards, as the
    Windows Clock does."""
    alarm["fired"] = stamp(when)
    alarm.pop("snoozed", None)
    if not alarm.get("days"):
        alarm["enabled"] = False


def snooze(alarm, now):
    minutes = int(alarm.get("snooze", 10) or 10)
    alarm["snoozed"] = stamp(now + datetime.timedelta(minutes=minutes))
    alarm["enabled"] = True


def timer_left(timer, now_epoch):
    """Seconds left on a timer at `now_epoch` (float, may be 0)."""
    state = timer.get("state", "idle")
    if state == "running":
        return max(0.0, float(timer.get("end", 0)) - now_epoch)
    if state == "paused":
        return max(0.0, float(timer.get("left", timer.get("seconds", 0))))
    return float(timer.get("seconds", 0))


def due_timers(data, now_epoch):
    return [t for t in data.get("timers", []) if t.get("state") == "running"
            and float(t.get("end", 0)) <= now_epoch and not t.get("rang")]


def start_timer(timer, now_epoch):
    left = timer_left(timer, now_epoch) if timer.get("state") == "paused" else float(timer.get("seconds", 0))
    timer.update({"state": "running", "end": now_epoch + left, "rang": False})
    timer.pop("left", None)


def pause_timer(timer, now_epoch):
    if timer.get("state") == "running":
        timer.update({"state": "paused", "left": timer_left(timer, now_epoch)})
        timer.pop("end", None)


def reset_timer(timer):
    timer.update({"state": "idle", "rang": False})
    timer.pop("end", None)
    timer.pop("left", None)


def format_duration(seconds, with_hours=None):
    """"1:05:09" / "05:09", for timers and the stopwatch."""
    seconds = max(0, int(round(seconds)))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours or with_hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def repeat_text(days, lang="en"):
    """"Only once", "Every day", "Weekdays", "Weekends" or the days."""
    days = sorted({int(d) for d in days if isinstance(d, int) and 0 <= d <= 6})
    names_tr = ("Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz")
    if not days:
        return "Yalnızca bir kez" if lang == "tr" else "Only once"
    if days == list(range(7)):
        return "Her gün" if lang == "tr" else "Every day"
    if days == list(range(5)):
        return "Hafta içi" if lang == "tr" else "Weekdays"
    if days == [5, 6]:
        return "Hafta sonu" if lang == "tr" else "Weekends"
    names = names_tr if lang == "tr" else DAY_NAMES
    return ", ".join(names[d] for d in days)
