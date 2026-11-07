"""Acrylic behind VeltOS Settings' window (acrylic.py): the blurred region,
what is sent to KWindowEffects, and the backend's switch (no KWin needed:
the library's functions are replaced by recorders)."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QCoreApplication, QPoint
    from PySide6.QtGui import QGuiApplication, QWindow
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


class Recorder:
    def __init__(self, result=True):
        self.calls = []
        self.result = result

    def __call__(self, *args):
        self.calls.append(args)
        return self.result


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class AcrylicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def fake(self, available=True):
        from veltos_settings import acrylic
        effects = acrylic.Acrylic(library="libdoes-not-exist.so")
        self.assertFalse(effects.supported())          # no library: Mica instead
        self.assertFalse(effects.apply(QWindow(), None))
        effects._blur, effects._contrast, effects._available = Recorder(), Recorder(), Recorder(available)
        return effects

    def test_rounded_region_leaves_the_corners_out(self):
        from veltos_settings import acrylic
        region = acrylic.frame_region(1144, 764, 12)
        self.assertTrue(region.contains(QPoint(572, 382)))
        self.assertTrue(region.contains(QPoint(12 + 8, 12)))            # top edge after the curve
        self.assertFalse(region.contains(QPoint(12, 12)))               # the rounded corner itself
        self.assertFalse(region.contains(QPoint(5, 400)))               # the shadow margin
        self.assertEqual(region.boundingRect().getRect(), (12, 12, 1120, 740))
        square = acrylic.frame_region(1920, 1040, 0)                    # maximized: no margin, square
        self.assertTrue(square.contains(QPoint(0, 0)))
        self.assertTrue(acrylic.rounded_region(0, 0, 0, 10, 8).isEmpty())

    def test_apply_blurs_and_sets_the_mode_contrast(self):
        from veltos_settings import acrylic
        effects = self.fake()
        self.assertTrue(effects.supported())
        self.assertEqual(effects._available.calls, [(acrylic.BLUR_BEHIND,)])
        window = QWindow()
        region = acrylic.frame_region(400, 300, 12)
        self.assertTrue(effects.apply(window, region, dark=True))
        blur, contrast = effects._blur.calls[-1], effects._contrast.calls[-1]
        self.assertTrue(blur[1])
        self.assertEqual(contrast[1:5], (True, *acrylic.CONTRAST_VALUES[True]))
        effects.apply(window, region, dark=False)
        self.assertEqual(effects._contrast.calls[-1][2:5], acrylic.CONTRAST_VALUES[False])
        # Dark mode darkens what is behind, light mode brightens it.
        self.assertLess(acrylic.CONTRAST_VALUES[True][1], 1)
        self.assertGreater(acrylic.CONTRAST_VALUES[False][1], 1)
        effects.apply(window, None)
        self.assertFalse(effects._blur.calls[-1][1])
        self.assertFalse(effects._contrast.calls[-1][1])

    def test_backend_follows_transparency_and_kwin(self):
        from fakesystem import FakeSystem
        from veltos_settings import acrylic
        from veltos_settings import app as settings_app
        backend = settings_app.Backend(lang="en", start=lambda command, env=None: None,
                                       system=settings_app.system_tools(FakeSystem()), threaded=False)
        self.assertFalse(backend.property("acrylic"))                   # no KWin effects given
        effects = self.fake()
        backend.use_acrylic(effects)
        self.assertTrue(backend.property("transparency"))
        self.assertTrue(backend.property("acrylic"))
        window = QWindow()
        window.setProperty("shadow", 12)
        window.resize(400, 300)
        acrylic.follow(window, backend, effects)
        QCoreApplication.processEvents()
        self.assertTrue(effects._blur.calls[-1][1])
        backend.setPref("transparency", False)                          # Transparency effects off
        self.assertFalse(backend.property("acrylic"))
        self.assertFalse(effects._blur.calls[-1][1])
        effects._available.result = False                               # KWin without blur
        backend.setPref("transparency", True)
        self.assertFalse(backend.property("acrylic"))


if __name__ == "__main__":
    unittest.main()
