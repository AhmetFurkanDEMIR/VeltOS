"""Windows 11's acrylic for VeltOS Settings' self-drawn window: KWin blurs
what is behind the window (other windows, the desktop) and its contrast
effect darkens (dark mode) or brightens (light mode) it, under the window's
own translucent colour (Theme.acrylicTint).

KWindowEffects (KF6 WindowSystem) has no Python binding. Its functions are
called through ctypes with the C++ pointers of the PySide6 objects: Debian's
PySide6 uses the same Qt libraries as KF6 (checked in the dev VM,
2026-11-07). KWindowSystem's Wayland plugin keeps the request and applies it
again when the window's surface is made anew or KWin's blur comes back.
Without the library, outside a Wayland session or without KWin's blur,
`supported()` is False and the window shows its Mica (the desktop picture)
instead.
"""

import ctypes

from PySide6.QtCore import QRect, QTimer
from PySide6.QtGui import QRegion

try:
    import shiboken6
except ImportError:          # pragma: no cover (PySide6 always has it)
    shiboken6 = None

LIBRARY = "libKF6WindowSystem.so.6"
# KWindowEffects' functions (nm -D libKF6WindowSystem.so.6, KF6 6.13).
BLUR = "_ZN14KWindowEffects16enableBlurBehindEP7QWindowbRK7QRegion"
CONTRAST = "_ZN14KWindowEffects24enableBackgroundContrastEP7QWindowbdddRK7QRegion"
AVAILABLE = "_ZN14KWindowEffects17isEffectAvailableENS_6EffectE"
BLUR_BEHIND = 7                 # KWindowEffects::BlurBehind
# The contrast effect under the window (contrast, intensity, saturation), the
# values of the VeltOS Plasma themes' acrylic (veltos-desktop tools/fluent.py).
CONTRAST_VALUES = {False: (0.7, 1.15, 1.8), True: (0.75, 0.5, 2.2)}
RADIUS = 8


def rounded_region(x, y, width, height, radius):
    """The window's rounded rectangle as a QRegion (KWin blurs exactly this)."""
    if width <= 0 or height <= 0:
        return QRegion()
    radius = max(0, min(radius, width // 2, height // 2))
    if radius == 0:
        return QRegion(x, y, width, height)
    region = QRegion(x + radius, y, width - 2 * radius, height)
    region = region.united(QRegion(x, y + radius, width, height - 2 * radius))
    size = 2 * radius
    for cx, cy in ((x, y), (x + width - size, y), (x, y + height - size), (x + width - size, y + height - size)):
        region = region.united(QRegion(QRect(cx, cy, size, size), QRegion.RegionType.Ellipse))
    return region


def frame_region(width, height, margin):
    """The frame inside the window's shadow margin; square when maximized."""
    return rounded_region(margin, margin, width - 2 * margin, height - 2 * margin, RADIUS if margin else 0)


class Acrylic:
    def __init__(self, library=LIBRARY):
        self._blur = self._contrast = self._available = None
        if shiboken6 is None:
            return
        try:
            lib = ctypes.CDLL(library)
            blur = getattr(lib, BLUR)
            contrast = getattr(lib, CONTRAST)
            available = getattr(lib, AVAILABLE)
        except (OSError, AttributeError):
            return
        blur.restype = None
        blur.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_void_p]
        contrast.restype = None
        contrast.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_double, ctypes.c_double,
                             ctypes.c_double, ctypes.c_void_p]
        available.restype = ctypes.c_bool
        available.argtypes = [ctypes.c_int]
        self._blur, self._contrast, self._available = blur, contrast, available

    def supported(self):
        """KWin offers blur behind windows now (a Wayland session with the effect loaded)."""
        return self._available is not None and bool(self._available(BLUR_BEHIND))

    def apply(self, window, region=None, dark=False):
        """Blur and contrast behind `region` of the window; None turns both off."""
        if self._blur is None:
            return False
        on = region is not None
        region = region if on else QRegion()
        window_ptr = shiboken6.getCppPointer(window)[0]
        region_ptr = shiboken6.getCppPointer(region)[0]
        self._blur(window_ptr, on, region_ptr)
        self._contrast(window_ptr, on, *CONTRAST_VALUES[bool(dark)], region_ptr)
        return True


def follow(window, backend, acrylic):
    """Keep the blur on the window's frame while the backend's `acrylic` is
    on: after resizing, maximizing, a light/dark switch and Transparency
    effects."""
    state = {"region": None}

    def update(*_args):
        if not backend.property("acrylic"):
            if state["region"] is not None:
                acrylic.apply(window, None)
                state["region"] = None
            return
        margin = int(window.property("shadow") or 0)
        region = frame_region(window.width(), window.height(), margin)
        acrylic.apply(window, region, backend.property("darkMode"))
        state["region"] = region

    for signal in (window.widthChanged, window.heightChanged, window.visibilityChanged,
                   backend.acrylicChanged):
        signal.connect(update)
    # The surface exists once the window is shown.
    QTimer.singleShot(0, update)
    return update
