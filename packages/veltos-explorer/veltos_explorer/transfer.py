"""Copying and moving files with progress, as Windows 11's copy window
shows it (transferwindow.py draws the window; this module has no Qt).

A transfer is planned first (every file, folder and link with its size),
then run file by file in 1 MiB pieces so the window can show the percent,
the speed, the time and items remaining, and pause or cancel between any
two pieces. Windows' rules:

- a copy into the folder it comes from gets "name - Copy" (files.copy_name);
- an item that already exists at the destination is a conflict: the window
  asks "Replace or Skip Files" (the answer may count for all of them);
- a move on one drive is a rename (instant); between drives it is a copy,
  and the originals go once everything is copied;
- an item cannot be copied or moved into itself.

Errors (no permission, a full disk) are collected and reported at the end;
the rest goes on. A cancelled copy leaves no half-written file behind.
"""

import os
import shutil
import threading
import time
from pathlib import Path

try:
    from . import files
except ImportError:  # pragma: no cover - run from the source tree
    import files

CHUNK = 1 << 20
REPLACE, SKIP = "replace", "skip"


class Item:
    """One thing to create at the destination."""

    __slots__ = ("kind", "source", "target", "size", "top")

    def __init__(self, kind, source, target, size=0, top=None):
        self.kind = kind            # "file", "dir", "link"
        self.source = source
        self.target = target
        self.size = size
        self.top = top              # the top-level source it belongs to


def same_device(a, b):
    try:
        return os.stat(a).st_dev == os.stat(b).st_dev
    except OSError:
        return False


def plan(sources, destination, mode="copy"):
    """(items, renames, problems): what to create, the top-level moves that
    are plain renames, and sources that cannot go there."""
    destination = os.path.abspath(destination)
    items, renames, problems = [], [], []
    for source in sources:
        source = os.path.abspath(source.rstrip("/") or source)
        if not os.path.lexists(source):
            problems.append((source, "missing"))
            continue
        name = os.path.basename(source)
        is_dir = os.path.isdir(source) and not os.path.islink(source)
        if is_dir and (destination == source or destination.startswith(source + os.sep)):
            problems.append((source, "into_itself"))
            continue
        parent = os.path.dirname(source)
        if parent == destination:
            if mode == "move":
                continue                       # already there
            name = files.copy_name(destination, name, is_dir)
        target = os.path.join(destination, name)
        if mode == "move" and same_device(source, destination) and not os.path.lexists(target):
            renames.append((source, target))
            continue
        _walk(source, target, source, items)
    return items, renames, problems


def _walk(source, target, top, items):
    if os.path.islink(source):
        items.append(Item("link", source, target, 0, top))
    elif os.path.isdir(source):
        items.append(Item("dir", source, target, 0, top))
        try:
            entries = sorted(os.listdir(source))
        except OSError:
            entries = []
        for entry in entries:
            _walk(os.path.join(source, entry), os.path.join(target, entry), top, items)
    else:
        try:
            size = os.stat(source).st_size
        except OSError:
            size = 0
        items.append(Item("file", source, target, size, top))


class Transfer:
    """Runs a plan. `progress` is called (from the worker thread) with
    nothing; read the attributes. `ask(item)` returns (REPLACE or SKIP,
    apply_to_all) for a conflict; it may block until the user answers."""

    def __init__(self, sources, destination, mode="copy", ask=None, progress=None, clock=time.monotonic):
        self.mode = mode
        self.destination = os.path.abspath(destination)
        self.sources = [os.path.abspath(s) for s in sources]
        self.items, self.renames, self.problems = plan(sources, destination, mode)
        self.total_bytes = sum(i.size for i in self.items)
        self.total_items = sum(1 for i in self.items if i.kind != "dir") + len(self.renames)
        self.done_bytes = 0
        self.done_items = 0
        self.current = ""
        self.errors = []            # (path, message)
        self.skipped = 0
        self.cancelled = False
        self.finished = False
        self._ask = ask or (lambda item: (SKIP, False))
        self._progress = progress or (lambda: None)
        self._clock = clock
        self._run = threading.Event()
        self._run.set()
        self._cancel = threading.Event()
        self._decision = None       # an answer for all conflicts
        self._samples = []          # (time, bytes) for the speed
        self._failed_tops = set()

    # --- control from the window ----------------------------------------------

    def pause(self):
        self._run.clear()

    def resume(self):
        self._run.set()

    @property
    def paused(self):
        return not self._run.is_set()

    def cancel(self):
        self._cancel.set()
        self._run.set()

    # --- figures ----------------------------------------------------------------

    @property
    def fraction(self):
        if self.total_bytes:
            return min(1.0, self.done_bytes / self.total_bytes)
        return min(1.0, self.done_items / self.total_items) if self.total_items else 1.0

    def speed(self):
        """Bytes per second over the last few seconds."""
        if len(self._samples) < 2:
            return 0.0
        (t0, b0), (t1, b1) = self._samples[0], self._samples[-1]
        return (b1 - b0) / (t1 - t0) if t1 > t0 else 0.0

    def seconds_left(self):
        speed = self.speed()
        if speed <= 0:
            return None
        return (self.total_bytes - self.done_bytes) / speed

    def _sample(self):
        now = self._clock()
        self._samples.append((now, self.done_bytes))
        while len(self._samples) > 2 and now - self._samples[0][0] > 3:
            self._samples.pop(0)

    # --- the work ---------------------------------------------------------------

    def _wait(self):
        """Between pieces: stop while paused; False when cancelled."""
        self._run.wait()
        return not self._cancel.is_set()

    def run(self):
        try:
            for source, target in self.renames:
                if not self._wait():
                    break
                self.current = os.path.basename(source)
                try:
                    os.rename(source, target)
                    self.done_items += 1
                except OSError as error:
                    self.errors.append((source, error.strerror or str(error)))
                self._progress()
            skip_below = None
            for item in self.items:
                if not self._wait():
                    break
                if skip_below and (item.source + os.sep).startswith(skip_below):
                    continue
                skip_below = None
                self.current = os.path.basename(item.source)
                result = self._one(item)
                if result == "skip-dir":
                    skip_below = item.source + os.sep
                self._sample()
                self._progress()
            if self.mode == "move" and not self._cancel.is_set():
                self._remove_moved()
        finally:
            self.cancelled = self._cancel.is_set()
            self.finished = True
            self._sample()
            self._progress()

    def _conflict(self, item):
        """REPLACE or SKIP for an item whose target exists."""
        if self._decision:
            return self._decision
        answer, for_all = self._ask(item)
        if for_all:
            self._decision = answer
        return answer

    def _one(self, item):
        try:
            if item.kind == "dir":
                if os.path.lexists(item.target) and not os.path.isdir(item.target):
                    if self._conflict(item) == SKIP:
                        self.skipped += 1
                        self._failed_tops.add(item.top)
                        return "skip-dir"
                    os.remove(item.target)
                os.makedirs(item.target, exist_ok=True)
                try:
                    shutil.copystat(item.source, item.target)
                except OSError:
                    pass
                return "ok"
            if os.path.lexists(item.target):
                if os.path.samefile(item.source, item.target) if os.path.exists(item.target) else False:
                    self.skipped += 1
                    self._failed_tops.add(item.top)
                    return "skip"
                if self._conflict(item) == SKIP:
                    self.skipped += 1
                    self.done_bytes += item.size
                    self.done_items += 1
                    self._failed_tops.add(item.top)
                    return "skip"
                if os.path.isdir(item.target) and not os.path.islink(item.target):
                    shutil.rmtree(item.target)
                else:
                    os.remove(item.target)
            if item.kind == "link":
                os.symlink(os.readlink(item.source), item.target)
                self.done_items += 1
                return "ok"
            self._copy_file(item)
            self.done_items += 1
            return "ok"
        except OSError as error:
            self.errors.append((item.source, error.strerror or str(error)))
            self._failed_tops.add(item.top)
            self.done_bytes += item.size if item.kind == "file" else 0
            return "error"

    def _copy_file(self, item):
        start = self.done_bytes
        partial = item.target + ".veltos-part"
        try:
            with open(item.source, "rb") as src, open(partial, "wb") as dst:
                while True:
                    if not self._wait():
                        raise InterruptedError
                    chunk = src.read(CHUNK)
                    if not chunk:
                        break
                    dst.write(chunk)
                    self.done_bytes += len(chunk)
                    self._sample()
                    self._progress()
            shutil.copystat(item.source, partial)
            os.replace(partial, item.target)
        except InterruptedError:
            self.done_bytes = start
            _unlink(partial)
        except OSError:
            self.done_bytes = start
            _unlink(partial)
            raise

    def _remove_moved(self):
        """A move between drives: the originals go once they are copied
        (not the ones with a skipped or failed item inside)."""
        for top in self.sources:
            if top in self._failed_tops or not any(i.top == top for i in self.items):
                continue
            try:
                if os.path.isdir(top) and not os.path.islink(top):
                    shutil.rmtree(top)
                else:
                    os.remove(top)
            except OSError as error:
                self.errors.append((top, error.strerror or str(error)))


def _unlink(path):
    try:
        os.remove(path)
    except OSError:
        pass


def duration_text(seconds, lang="en"):
    """Windows' "About 2 minutes" / "Yaklaşık 2 dakika"."""
    tr = lang == "tr"
    if seconds is None:
        return "Hesaplanıyor…" if tr else "Calculating…"
    seconds = int(seconds + 0.5)
    if seconds < 60:
        n = max(1, (seconds + 4) // 5 * 5)
        return f"Yaklaşık {n} saniye" if tr else f"About {n} second{'s' if n != 1 else ''}"
    if seconds < 3600:
        n = (seconds + 30) // 60
        return f"Yaklaşık {n} dakika" if tr else f"About {n} minute{'s' if n != 1 else ''}"
    hours, minutes = divmod((seconds + 30) // 60, 60)
    if tr:
        return f"Yaklaşık {hours} saat {minutes} dakika" if minutes else f"Yaklaşık {hours} saat"
    text = f"About {hours} hour{'s' if hours != 1 else ''}"
    return text + (f" {minutes} minute{'s' if minutes != 1 else ''}" if minutes else "")
