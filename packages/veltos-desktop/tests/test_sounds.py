"""The VeltOS sound theme (tools/sounds.py): original sounds under the
freedesktop names Plasma and GTK programs ask for."""

import sys
import tempfile
import unittest
import wave
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PKG / "tools"))
import sounds  # noqa: E402


class SoundThemeTests(unittest.TestCase):
    def test_theme_has_the_events_plasma_uses(self):
        names = set(sounds.SOUNDS) | set(sounds.ALIASES)
        for event in ("desktop-login", "desktop-logout", "message-new-instant", "dialog-error",
                      "dialog-warning", "dialog-information", "device-added", "device-removed",
                      "power-plug", "power-unplug", "battery-caution", "battery-low"):
            self.assertIn(event, names)
        for target in sounds.ALIASES.values():
            self.assertIn(target, sounds.SOUNDS)

    def test_notification_sound_is_short_and_not_clipped(self):
        frames = sounds.render(sounds.SOUNDS["message-new-instant"])
        samples = [int.from_bytes(frames[i:i + 2], "little", signed=True) for i in range(0, len(frames), 2)]
        self.assertLess(len(samples) / sounds.RATE, 2.0)
        self.assertLessEqual(max(abs(s) for s in samples), 32767 * 0.71)
        self.assertEqual(samples[-1], 0)                     # faded out, no click

    def test_build_writes_wav_files_and_index(self):
        root = Path(tempfile.mkdtemp())
        base = sounds.build(root)
        self.assertIn("Inherits=ocean,freedesktop", (base / "index.theme").read_text())
        with wave.open(str(base / "stereo/desktop-login.wav")) as w:
            self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, sounds.RATE))
        self.assertTrue((base / "stereo/bell.wav").is_symlink())


if __name__ == "__main__":
    unittest.main()
