"""Programs' permission and account requests through the desktop portal in
VeltOS' question window instead of KDE's dialogs (portal.py Access and
Account, app.py --question; product owner, 2026-10-31)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from veltos_explorer import portal  # noqa: E402

try:
    from veltos_explorer import app as explorer_app
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


class PortalQuestionTests(unittest.TestCase):
    def test_app_names_come_from_desktop_files(self):
        with tempfile.TemporaryDirectory() as folder:
            apps = Path(folder) / "applications"
            apps.mkdir()
            (apps / "com.usebottles.bottles.desktop").write_text(
                "[Desktop Entry]\nName=Bottles\nName[tr]=Şişeler\n\n[Desktop Action new]\nName=New\n",
                encoding="utf-8")
            self.assertEqual(portal.app_name("com.usebottles.bottles", [folder], "en"), "Bottles")
            self.assertEqual(portal.app_name("com.usebottles.bottles", [folder], "tr"), "Şişeler")
            self.assertEqual(portal.app_name("org.unknown.App", [folder], "en"), "org.unknown.App")
        self.assertEqual(portal.app_name("", []), "")

    def test_access_request(self):
        request = portal.access_question("", "", "Allow camera access?", "The app wants the camera.",
                                         "You can change this later.", {"grant_label": "Allow camera"})
        self.assertEqual(request["kind"], "access")
        self.assertEqual(request["heading"], "Allow camera access?")
        self.assertEqual(request["text"], "The app wants the camera.\n\nYou can change this later.")
        self.assertEqual(request["yes"], "Allow camera")
        self.assertEqual(request["no"], "")

    def test_answers(self):
        self.assertEqual(portal.question_results(portal.ACCESS_IFACE, "yes"), (portal.SUCCESS, {}))
        self.assertEqual(portal.question_results(portal.ACCESS_IFACE, ""), (portal.CANCELLED, {}))
        code, results = portal.question_results(portal.ACCOUNT_IFACE, "yes")
        self.assertEqual(code, portal.SUCCESS)
        self.assertEqual(sorted(results), ["id", "image", "name"])
        self.assertTrue(results["id"])
        self.assertEqual(portal.question_results(portal.ACCOUNT_IFACE, "no"), (portal.CANCELLED, {}))

    def test_interfaces_in_the_backend(self):
        import xml.etree.ElementTree as ET
        names = [i.get("name") for i in ET.fromstring(portal.NODE_XML.replace("{{", "{").replace("}}", "}"))
                 .findall("interface")]
        self.assertIn(portal.ACCESS_IFACE, names)
        self.assertIn(portal.ACCOUNT_IFACE, names)

    @unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
    def test_window_texts(self):
        access = explorer_app.portal_question({"kind": "access", "heading": "Allow?", "text": "Camera",
                                               "app": "Bottles"}, "en")
        self.assertEqual((access.heading, access.question, access.yesLabel, access.noLabel),
                         ("Allow?", "Camera", "Allow", "Don't allow"))
        account = explorer_app.portal_question({"kind": "account", "app": "Bottles",
                                                "user": {"id": "ali", "name": "Ali Veli"},
                                                "reason": "To fill in your name."}, "tr")
        self.assertEqual(account.heading, "Bilgilerinizi paylaşın")
        self.assertIn("Ali Veli (ali)", account.question)
        self.assertIn("To fill in your name.", account.question)
        self.assertEqual((account.yesLabel, account.noLabel), ("Paylaş", "İptal"))


if __name__ == "__main__":
    unittest.main()
