"""The portal backend hands its dialogs KDE's platform theme, not the
portal's: the session sets QT_QPA_PLATFORMTHEME=xdgdesktopportal for every
program, and the portal's own dialog must not ask the portal (2026-10-22).
No Qt needed here: the switch is plain environment."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_explorer import app  # noqa: E402


class PortalThemeTests(unittest.TestCase):
    def test_backend_switches_to_the_kde_theme(self):
        environ = {"QT_QPA_PLATFORMTHEME": "xdgdesktopportal", "HOME": "/home/velt"}
        self.assertEqual(app.portal_platform_theme(environ), "kde")
        self.assertEqual(environ["QT_QPA_PLATFORMTHEME"], "kde")
        self.assertEqual(environ["HOME"], "/home/velt")       # nothing else touched

    def test_sets_the_theme_when_none_was_given(self):
        environ = {}
        app.portal_platform_theme(environ)
        self.assertEqual(environ, {"QT_QPA_PLATFORMTHEME": "kde"})

    def test_default_is_the_process_environment(self):
        before = os.environ.get("QT_QPA_PLATFORMTHEME")
        try:
            os.environ["QT_QPA_PLATFORMTHEME"] = "xdgdesktopportal"
            app.portal_platform_theme()
            self.assertEqual(os.environ["QT_QPA_PLATFORMTHEME"], "kde")
        finally:
            if before is None:
                os.environ.pop("QT_QPA_PLATFORMTHEME", None)
            else:
                os.environ["QT_QPA_PLATFORMTHEME"] = before


if __name__ == "__main__":
    unittest.main()
