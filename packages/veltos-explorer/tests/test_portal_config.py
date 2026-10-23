"""The xdg-desktop-portal configuration VeltOS installs for Plasma sessions."""

import configparser
import unittest
from pathlib import Path

CONF = Path(__file__).resolve().parent.parent / "data/kde-portals.conf"


class PortalConfigTests(unittest.TestCase):
    def setUp(self):
        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser.read(CONF, encoding="utf-8")
        self.preferred = parser["preferred"]

    def test_file_dialogs_come_from_file_explorer(self):
        self.assertEqual(self.preferred["default"], "kde")
        self.assertEqual(self.preferred["org.freedesktop.impl.portal.FileChooser"], "veltos")

    def test_no_gtk_backend_at_sign_in(self):
        # Without these the portal started the GTK backend as a fallback
        # (Lockdown) and for Settings; it waits for graphical-session.target,
        # so early portal requests at sign-in waited 25 s (2026-10-22).
        self.assertEqual(self.preferred["org.freedesktop.impl.portal.Settings"], "kde")
        self.assertEqual(self.preferred["org.freedesktop.impl.portal.Lockdown"], "none")
        self.assertNotIn("gtk", " ".join(self.preferred.values()))


if __name__ == "__main__":
    unittest.main()
