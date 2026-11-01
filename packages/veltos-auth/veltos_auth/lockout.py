"""Waiting after wrong passwords (product owner, 2026-11-01): three wrong
passwords in a row lock the prompt for 30 seconds, three more for a
minute, and every further three for two minutes; the right password
starts the count again.

The count is the user's own and lives in the session's runtime folder
($XDG_RUNTIME_DIR/veltos/password-failures.json), so every VeltOS
password prompt of the session shares it and it goes with the session.
The sign-in and lock screens keep the same rule in their QML.
"""

import json
import os
import time
from pathlib import Path

PER_STEP = 3


def delay_for(count):
    """Seconds to wait after the count-th wrong password (0 if none)."""
    if count <= 0 or count % PER_STEP:
        return 0
    step = count // PER_STEP
    return 30 if step == 1 else 60 if step == 2 else 120


def state_file(environ=None):
    environ = os.environ if environ is None else environ
    runtime = environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return Path(runtime) / "veltos" / "password-failures.json"


def load(path=None):
    try:
        data = json.loads(Path(path or state_file()).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"count": 0, "until": 0}
    if not isinstance(data, dict):
        return {"count": 0, "until": 0}
    return {"count": int(data.get("count", 0) or 0), "until": float(data.get("until", 0) or 0)}


def save(data, path=None):
    path = Path(path or state_file())
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass


def remaining(path=None, now=None):
    """Seconds the prompt still waits (0: it may be used)."""
    left = load(path)["until"] - (time.time() if now is None else now)
    return max(0, int(left + 0.999))


def failed(path=None, now=None):
    """Records a wrong password; the seconds to wait now (0 if none)."""
    data = load(path)
    data["count"] += 1
    wait = delay_for(data["count"])
    if wait:
        data["until"] = (time.time() if now is None else now) + wait
    save(data, path)
    return wait


def succeeded(path=None):
    save({"count": 0, "until": 0}, path)
