"""The play queue of VeltOS Media Player: what plays next with shuffle and
repeat (off, all, one), as Windows 11 Media Player does. Plain logic,
tested without Qt."""

import random

REPEAT_MODES = ("off", "all", "one")


class PlayQueue:
    def __init__(self, rng=None):
        self.items = []          # entries (dicts with "path")
        self.index = -1          # position in `order`
        self.order = []          # indexes into items, shuffled or not
        self.shuffle = False
        self.repeat = "off"
        self._rng = rng or random.Random()

    @property
    def current(self):
        if 0 <= self.index < len(self.order):
            return self.items[self.order[self.index]]
        return None

    def _reorder(self, keep=None):
        self.order = list(range(len(self.items)))
        if self.shuffle and self.order:
            self._rng.shuffle(self.order)
            if keep is not None and keep in self.order:
                # The playing item stays first, the rest is shuffled after it.
                self.order.remove(keep)
                self.order.insert(0, keep)
        self.index = self.order.index(keep) if keep is not None and keep in self.order else (0 if self.order else -1)

    def play(self, items, start=0):
        """Replace the queue and start at `start`."""
        self.items = list(items)
        start = start if 0 <= start < len(self.items) else 0
        self._reorder(keep=start if self.items else None)
        return self.current

    def add(self, items):
        """Add to the end ("Add to play queue")."""
        first = not self.items
        base = len(self.items)
        self.items.extend(items)
        new = list(range(base, len(self.items)))
        if self.shuffle:
            self._rng.shuffle(new)
        self.order.extend(new)
        if first and self.items:
            self.index = 0
        return self.current

    def remove(self, position):
        """Remove the item at a queue position (as shown, in play order)."""
        if not 0 <= position < len(self.order):
            return self.current
        removed = self.order.pop(position)
        self.items.pop(removed)
        self.order = [i - 1 if i > removed else i for i in self.order]
        if position < self.index:
            self.index -= 1
        self.index = min(self.index, len(self.order) - 1)
        return self.current

    def clear(self):
        self.items, self.order, self.index = [], [], -1

    def set_shuffle(self, on):
        if on != self.shuffle:
            self.shuffle = on
            keep = self.order[self.index] if 0 <= self.index < len(self.order) else None
            self._reorder(keep)

    def cycle_repeat(self):
        self.repeat = REPEAT_MODES[(REPEAT_MODES.index(self.repeat) + 1) % len(REPEAT_MODES)]
        return self.repeat

    def go(self, position):
        if 0 <= position < len(self.order):
            self.index = position
        return self.current

    def next(self, finished=False):
        """The next item. `finished`: the current one ended by itself (then
        repeat-one plays it again); None when the queue is over."""
        if not self.order:
            return None
        if finished and self.repeat == "one":
            return self.current
        if self.index + 1 < len(self.order):
            self.index += 1
            return self.current
        if self.repeat == "all":
            self.index = 0
            return self.current
        return None              # the end of the queue

    def has_next(self):
        """Whether Next would play something (the desktop's media controls
        grey their button out otherwise)."""
        return bool(self.order) and (self.index + 1 < len(self.order) or self.repeat == "all")

    def previous(self):
        if not self.order:
            return None
        if self.index > 0:
            self.index -= 1
        elif self.repeat == "all":
            self.index = len(self.order) - 1
        return self.current

    def in_order(self):
        """The queue as it will play."""
        return [self.items[i] for i in self.order]
