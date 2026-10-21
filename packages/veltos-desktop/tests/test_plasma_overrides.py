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
        self.source = self.tmp / "share"
        applets = self.source / "plasma/plasmoids"
        shutil.copytree(PKG / "tests/data/systemtray", applets / TRAY)
        shutil.copytree(PKG / "tests/data/notifications", applets / "org.kde.plasma.notifications")
        shutil.copytree(PKG / "tests/data/devicenotifier", applets / "org.kde.plasma.devicenotifier")
        shutil.copytree(PKG / "tests/data/taskmanager", applets / "org.kde.plasma.taskmanager")
        shutil.copytree(PKG / "tests/data/shell", self.source / "plasma/shells/org.kde.plasma.desktop")
        shutil.copytree(PKG / "tests/data/aurorae", self.source / "kwin/aurorae")
        self.out = self.tmp / "out"
        self.applets = self.out / "plasma/plasmoids"

    def run_tool(self, specs=PKG / "plasma-overrides"):
        return overrides.main(["--source", str(self.source), "--specs", str(specs),
                               "--out", str(self.out), "--check"])

    def test_tray_changes_apply_to_debian_plasma(self):
        self.assertEqual(self.run_tool(), 0)
        ui = self.applets / TRAY / "contents/ui"
        self.assertIn("visible: false // VeltOS", (ui / "items/AbstractItem.qml").read_text())
        self.assertIn("Math.min(4, count)) // VeltOS", (ui / "HiddenItemsView.qml").read_text())
        self.assertIn("visible: !!systemTrayState.activeApplet // VeltOS",
                      (ui / "ExpandedRepresentation.qml").read_text())
        self.assertTrue((self.applets / TRAY / overrides.MARKER).exists())

    def test_notification_changes_apply(self):
        self.assertEqual(self.run_tool(), 0)
        popup = self.applets / "org.kde.plasma.notifications/contents/ui/delegates/DelegatePopup.qml"
        self.assertIn("Windows toasts have no timeout bar", popup.read_text())
        self.assertIn("picture on the left, like Windows", popup.read_text())
        ui = self.applets / "org.kde.plasma.notifications/contents/ui"
        self.assertIn("popupLocation: Qt.AlignBottom | Qt.AlignRight", (ui / "global/Globals.qml").read_text())
        self.assertIn("equal widths filling the row", (ui / "components/ActionContainer.qml").read_text())
        self.assertIn("uniformCellSizes: true", (ui / "components/ActionContainer.qml").read_text())
        self.assertIn("objectAt(popupInstantiator.count - 1 - i)", (ui / "global/Globals.qml").read_text())
        self.assertIn("effectiveStatus: PlasmaCore.Types.HiddenStatus", (ui / "main.qml").read_text())

    def test_drives_flyout_changes_apply(self):
        self.assertEqual(self.run_tool(), 0)
        applet = self.applets / "org.kde.plasma.devicenotifier"
        self.assertIn('"Name[tr]": "Donanımı Güvenle Kaldır"', (applet / "metadata.json").read_text(encoding="utf-8"))
        self.assertIn("one list without headings", (applet / "contents/ui/FullRepresentation.qml").read_text())
        expanded = (self.applets / TRAY / "contents/ui/ExpandedRepresentation.qml").read_text()
        self.assertIn("Windows flyouts cannot be pinned", expanded)
        self.assertIn("veltosSmallApplet ? 10 : 24", expanded)
        self.assertIn("veltosSmallApplet ? veltosAppletHeight : Infinity", expanded)

    def test_taskbar_menu_changes_apply(self):
        self.assertEqual(self.run_tool(), 0)
        menu = (self.applets / "org.kde.plasma.taskmanager/contents/ui/ContextMenu.qml").read_text(encoding="utf-8")
        self.assertEqual(menu.count('"Pin to taskbar"'), 2)
        self.assertIn('"Unpin from taskbar"', menu)
        self.assertIn("VeltOS Settings has the taskbar options", menu)
        task = (self.applets / "org.kde.plasma.taskmanager/contents/ui/Task.qml").read_text(encoding="utf-8")
        self.assertIn("Windows shows no spinner on the taskbar button", task)
        self.assertIn("several windows of one app look like a stack of buttons", task)
        overlay = (self.applets / "org.kde.plasma.taskmanager/contents/ui/GroupExpanderOverlay.qml").read_text(
            encoding="utf-8")
        self.assertIn("visible: false // VeltOS", overlay)

    def test_changed_upstream_falls_back_to_plasma(self):
        self.run_tool()
        view = self.source / "plasma/plasmoids" / TRAY / "contents/ui/HiddenItemsView.qml"
        view.write_text(view.read_text().replace("readonly property int columns: 2", "property int columns: 3"))
        self.assertEqual(self.run_tool(), 1)            # --check reports it
        self.assertFalse((self.applets / TRAY).exists())    # Plasma's own version is used

    def test_lock_screen_replaced_while_plasma_file_unchanged(self):
        self.assertEqual(self.run_tool(), 0)
        shell = self.out / "plasma/shells/org.kde.plasma.desktop"
        ui = (shell / "contents/lockscreen/LockScreenUi.qml").read_text(encoding="utf-8")
        self.assertIn("VeltOS lock screen in the Windows 11 layout", ui)
        self.assertTrue((shell / "contents/lockscreen/LockScreen.qml").exists())   # the rest stays Plasma's
        original = self.source / "plasma/shells/org.kde.plasma.desktop/contents/lockscreen/LockScreenUi.qml"
        original.write_text(original.read_text(encoding="utf-8") + "// changed\n", encoding="utf-8")
        self.assertEqual(self.run_tool(), 1)
        self.assertFalse(shell.exists())        # Plasma's own lock screen is used

    def test_start_popup_is_centred_on_the_taskbar(self):
        self.assertEqual(self.run_tool(), 0)
        applet = (self.out / "plasma/shells/org.kde.plasma.desktop/contents/applet/CompactApplet.qml")
        text = applet.read_text(encoding="utf-8")
        self.assertIn("id: startCentre", text)
        self.assertIn('Plasmoid.pluginName === "org.veltos.startmenu"', text)
        self.assertNotIn("        visualParent: root.compactRepresentation\n", text)

    def test_window_frame_buttons_have_maximised_pictures(self):
        self.assertEqual(self.run_tool(), 0)
        button = (self.out / "kwin/aurorae/AuroraeButton.qml").read_text(encoding="utf-8")
        self.assertIn('prefix: "hover" + buttonSvg.maximizedSuffix', button)
        self.assertIn('prefix: "pressed" + buttonSvg.maximizedSuffix', button)
        self.assertIn('hasElementPrefix("hover-maximized")', button)

    def test_specs_are_complete(self):
        for path in sorted((PKG / "plasma-overrides").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(path.stem, data["plugin"])
            self.assertIn(data.get("type", "plasmoids"), overrides.TYPES)
            for change in data["replacements"]:
                self.assertTrue(change["why"])
                if "replace_with" in change:
                    self.assertTrue((PKG / "plasma-overrides/files" / change["replace_with"]).is_file())
                    self.assertRegex(change["upstream_sha256"], r"^[0-9a-f]{64}$")
                else:
                    self.assertNotEqual(change["old"], change["new"])


if __name__ == "__main__":
    unittest.main()
