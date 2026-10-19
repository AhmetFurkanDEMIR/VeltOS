"""update-plasma-overrides: the Windows 11 changes to Plasma components
apply to the Plasma QML of Debian 13 (copies in tests/data), and a change
that no longer fits leaves Plasma's own version in place."""

import importlib.machinery
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader("update_plasma_overrides",
                                              str(PKG / "system/update-plasma-overrides"))
spec = importlib.util.spec_from_loader(loader.name, loader)
overrides = importlib.util.module_from_spec(spec)
loader.exec_module(overrides)

TRAY = "org.kde.plasma.private.systemtray"


class OverrideTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.source = self.tmp / "plasmoids"
        shutil.copytree(PKG / "tests/data/systemtray", self.source / TRAY)
        self.out = self.tmp / "out"

    def run_tool(self, specs=PKG / "plasma-overrides"):
        return overrides.main(["--source", str(self.source), "--specs", str(specs),
                               "--out", str(self.out), "--check"])

    def test_tray_changes_apply_to_debian_plasma(self):
        self.assertEqual(self.run_tool(), 0)
        ui = self.out / TRAY / "contents/ui"
        self.assertIn("visible: false // VeltOS", (ui / "items/AbstractItem.qml").read_text())
        self.assertIn("columns: 4 // VeltOS", (ui / "HiddenItemsView.qml").read_text())
        self.assertIn("visible: !!systemTrayState.activeApplet // VeltOS",
                      (ui / "ExpandedRepresentation.qml").read_text())
        self.assertTrue((self.out / TRAY / overrides.MARKER).exists())

    def test_changed_upstream_falls_back_to_plasma(self):
        self.run_tool()
        view = self.source / TRAY / "contents/ui/HiddenItemsView.qml"
        view.write_text(view.read_text().replace("readonly property int columns: 2", "property int columns: 3"))
        self.assertEqual(self.run_tool(), 1)            # --check reports it
        self.assertFalse((self.out / TRAY).exists())    # Plasma's own version is used

    def test_specs_are_complete(self):
        for path in sorted((PKG / "plasma-overrides").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(path.stem, data["plugin"])
            for change in data["replacements"]:
                self.assertTrue(change["why"])
                self.assertNotEqual(change["old"], change["new"])


if __name__ == "__main__":
    unittest.main()
