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
        shutil.copytree(PKG / "tests/data/desktopcontainment", applets / "org.kde.desktopcontainment")
        shutil.copytree(PKG / "tests/data/panel", applets / "org.kde.panel")
        shutil.copytree(PKG / "tests/data/clipboard", applets / "org.kde.plasma.clipboard")
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
        self.assertIn("visible: !!systemTrayState.activeApplet && !popup.veltosOwnHeading // VeltOS",
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
        # Downloads and copies: Windows 11 progress and buttons, no Details/file menu.
        job = (ui / "components/JobItem.qml").read_text(encoding="utf-8")
        self.assertIn('i18nd("veltos-desktop", "Open folder")', job)
        self.assertIn("uniformCellSizes: true", job)
        self.assertNotIn("expandButton", job)
        self.assertNotIn("FileMenu", job)
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
        # Progress as a thin bar under the icon (whole file replaced).
        progress = (self.applets / "org.kde.plasma.taskmanager/contents/ui/TaskProgressOverlay.qml").read_text(
            encoding="utf-8")
        self.assertIn("thin bar under the icon", progress)
        self.assertIn("task.smartLauncherItem.progress", progress)

    def test_recycle_bin_shows_when_it_is_full(self):
        self.assertEqual(self.run_tool(), 0)
        ui = self.applets / "org.kde.desktopcontainment/contents/ui"
        delegate = (ui / "FolderItemDelegate.qml").read_text(encoding="utf-8")
        self.assertIn('(veltos.trashFull ? "user-trash-full" : "user-trash") : model.decoration', delegate)
        desktop = (ui / "VeltOSDesktop.qml").read_text(encoding="utf-8")
        self.assertIn('url: veltos.onDesktop ? "trash:/" : ""', desktop)

    def test_window_previews_come_from_kwin(self):
        self.assertEqual(self.run_tool(), 0)
        ui = self.applets / "org.kde.plasma.taskmanager/contents/ui"
        task = (ui / "Task.qml").read_text(encoding="utf-8")
        # Plasma's tooltip only for pinned apps that are not running.
        self.assertIn("&& !model.IsWindow // VeltOS: KWin's veltostaskbarpreview shows the windows", task)
        # The stack edge is drawn beside the plate only, in its colours.
        self.assertIn("x: frame.x + frame.width - frame.fixedMargins.right", task)
        self.assertIn("clip: true", task)
        self.assertNotIn("color: Qt.alpha(Kirigami.Theme.textColor, 0.05)", task)
        tools = (ui / "code/tools.js").read_text(encoding="utf-8")
        start = tools.index("if (model.IsGroupParent && modifiers !== null) {")
        self.assertLess(start, tools.index("Option 1 (default): Cycle through this group's tasks"))
        self.assertIn("return;", tools[start:start + 400])
        instance = (ui / "ToolTipInstance.qml").read_text(encoding="utf-8")
        self.assertIn('return ""; // VeltOS: Windows 11 names a pinned app, nothing more', instance)

    def test_playing_app_gets_a_round_speaker_badge(self):
        self.assertEqual(self.run_tool(), 0)
        badge = (self.applets / "org.kde.plasma.taskmanager/contents/ui/AudioStream.qml").read_text(encoding="utf-8")
        self.assertIn("radius: width / 2", badge)
        self.assertIn("toggleMuted()", badge)
        self.assertIn("loops: Animation.Infinite", badge)
        self.assertNotIn("audio-volume-high-symbolic", badge)

    def test_taskbar_menu_and_show_desktop_at_the_edge(self):
        self.assertEqual(self.run_tool(), 0)
        ui = self.applets / "org.kde.panel/contents/ui"
        main = (ui / "main.qml").read_text(encoding="utf-8")
        self.assertIn("    VeltOSTaskbarMenu {\n        anchors.fill: parent\n    }\n\n    DragDrop.DropArea {", main)
        self.assertIn("rightMargin: 0 // VeltOS", main)
        menu = (ui / "VeltOSTaskbarMenu.qml").read_text(encoding="utf-8")
        self.assertIn('shell.connectSource("veltos-taskmanager")', menu)
        self.assertIn('shell.connectSource("veltos-settings taskbar")', menu)
        self.assertIn("acceptedButtons: Qt.RightButton", menu)

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
        # Windows 11's sequence: the curtain goes up, "Welcome" with the
        # turning dots after the password, the time again after sleep.
        self.assertIn("id: curtain", ui)
        self.assertIn("component WindowsDots", ui)
        self.assertIn('ui.tr("Welcome", "Hoş geldiniz")', ui)
        self.assertIn("ui.finish();", ui)
        self.assertIn("ui.woke();", ui)
        self.assertTrue((shell / "contents/lockscreen/LockScreen.qml").exists())   # the rest stays Plasma's
        original = self.source / "plasma/shells/org.kde.plasma.desktop/contents/lockscreen/LockScreenUi.qml"
        original.write_text(original.read_text(encoding="utf-8") + "// changed\n", encoding="utf-8")
        self.assertEqual(self.run_tool(), 1)
        self.assertFalse(shell.exists())        # Plasma's own lock screen is used

    def test_taskbar_takes_the_accent_and_no_mouse_focus_box(self):
        self.assertEqual(self.run_tool(), 0)
        views = self.out / "plasma/shells/org.kde.plasma.desktop/contents/views"
        panel = (views / "Panel.qml").read_text(encoding="utf-8")
        self.assertIn("    TaskbarTint {\n        anchors.fill: floatingTranslucentItem\n", panel)
        self.assertIn("panel.activeFocusItem.focusReason === Qt.TabFocusReason", panel)
        self.assertNotIn("        visible: panel.active && panel.activeFocusItem\n\n", panel)
        tint = (views / "TaskbarTint.qml").read_text(encoding="utf-8")
        self.assertIn("Kirigami.Theme.highlightColor", tint)
        self.assertIn("ColorAnimation", tint)

    def test_osd_is_the_windows_flyout_at_the_bottom(self):
        self.assertEqual(self.run_tool(), 0)
        osd = self.out / "plasma/shells/org.kde.plasma.desktop/contents/osd"
        self.assertIn("windowScreenHeight: dialog.screen", (osd / "Osd.qml").read_text(encoding="utf-8"))
        item = (osd / "OsdItem.qml").read_text(encoding="utf-8")
        self.assertIn("anchors.bottom: parent.bottom", item)
        self.assertIn("Math.round(screenHeight * 2 / 3) - bottomBand * 2", item)
        self.assertIn('i18ndc("plasma_shell_org.kde.plasma.desktop"', item)

    def test_start_popup_is_centred_on_the_taskbar(self):
        self.assertEqual(self.run_tool(), 0)
        applet = (self.out / "plasma/shells/org.kde.plasma.desktop/contents/applet/CompactApplet.qml")
        text = applet.read_text(encoding="utf-8")
        self.assertIn("id: startCentre", text)
        self.assertIn('["org.veltos.startmenu", "org.veltos.search"].includes(Plasmoid.pluginName)', text)
        self.assertNotIn("        visualParent: root.compactRepresentation\n", text)
        # No box behind the search box while its window is open.
        self.assertIn('plasmoidItem.expanded && Plasmoid.pluginName !== "org.veltos.search" ? 1 : 0', text)

    def test_window_frame_buttons_have_maximised_pictures(self):
        self.assertEqual(self.run_tool(), 0)
        button = (self.out / "kwin/aurorae/AuroraeButton.qml").read_text(encoding="utf-8")
        self.assertIn('prefix: "hover" + buttonSvg.maximizedSuffix', button)
        self.assertIn('prefix: "pressed" + buttonSvg.maximizedSuffix', button)
        self.assertIn('hasElementPrefix("hover-maximized")', button)

    def test_office_windows_get_their_colour(self):
        # Microsoft 365's Word/Excel/PowerPoint have the app's colour in
        # the title bar; LibreOffice's windows behind VeltOS Office get it
        # from the frame (aurorae.json), with white caption and glyphs.
        self.assertEqual(self.run_tool(), 0)
        frame = (self.out / "kwin/aurorae/aurorae.qml").read_text(encoding="utf-8")
        self.assertIn("readonly property color veltosTint", frame)
        self.assertIn('caption.endsWith("VeltOS Office Calc")', frame)
        self.assertIn("color: root.veltosTint", frame)
        self.assertIn('root.veltosTinted ? (decoration.client.active ? "#FFFFFF"', frame)
        button = (self.out / "kwin/aurorae/AuroraeButton.qml").read_text(encoding="utf-8")
        self.assertIn('prefix: "active" + buttonSvg.tintSuffix', button)
        self.assertIn('prefix: "hover" + buttonSvg.maximizedSuffix + buttonSvg.tintSuffix', button)
        self.assertIn('hasElementPrefix("active-ondark")', button)

    def test_modal_dialogs_have_only_close(self):
        # Windows 11 message boxes have no Minimise/Maximise buttons.
        self.assertEqual(self.run_tool(), 0)
        button = (self.out / "kwin/aurorae/AuroraeButton.qml").read_text(encoding="utf-8")
        self.assertIn("visible = Qt.binding(() => buttonSvg.imagePath != \"\" && !(decoration.client.modal\n"
                      "                && buttonType == DecorationOptions.DecorationButtonMinimize));", button)
        maximize = (self.out / "kwin/aurorae/AuroraeMaximizeButton.qml").read_text(encoding="utf-8")
        self.assertIn("    visible: !decoration.client.modal\n    AuroraeButton {", maximize)

    def test_desktop_gets_windows_menus_and_protected_icons(self):
        self.assertEqual(self.run_tool(), 0)
        ui = self.applets / "org.kde.desktopcontainment/contents/ui"
        added = (ui / "VeltOSDesktop.qml").read_text(encoding="utf-8")
        self.assertIn('i18nd(domain, text)', added)
        self.assertIn('"recycle-bin.desktop", "this-pc.desktop", "veltos-store.desktop"', added)
        self.assertIn("/usr/libexec/veltos/desktop-new ", added)
        self.assertIn("veltos-explorer --empty-recycle-bin", added)
        view = (ui / "FolderView.qml").read_text(encoding="utf-8")
        self.assertIn("VeltOSDesktop {\n            id: veltos\n", view)
        self.assertIn("veltos.desktopMenu(listener.mapToItem(main, mouse.x, mouse.y));", view)
        self.assertIn("(dir.usedByContainment ? (Qt.LeftButton | Qt.RightButton) : Qt.LeftButton)", view)
        self.assertEqual(view.count("if (!veltos.itemMenu(hoveredItem, listener.mapToItem(main, mouse.x, mouse.y)))"), 2)
        self.assertEqual(view.count("veltos.selectionProtected()"), 4)     # Delete, trash, cut, rename
        self.assertNotIn("                        dir.refresh();\n", view)
        editor = (ui / "RenameEditor.qml").read_text(encoding="utf-8")
        self.assertIn("radius: 2\n", editor)
        self.assertIn("(Plasmoid.configuration.textLines + 8)", editor)
        self.assertNotIn("ScrollBar.vertical.policy = Qt.ScrollBarAlwaysOn;", editor)
        self.assertIn("readonly property string veltosFileName:", (ui / "FolderItemDelegate.qml").read_text(encoding="utf-8"))
        # Plasma's containment menu is reached from nowhere on the desktop.
        self.assertNotIn("if (!dir.usedByContainment) {\n                        dir.openContextMenu(main", view)
        # A file Plasma gained itself is not overwritten: the whole change is dropped.
        (self.source / "plasma/plasmoids/org.kde.desktopcontainment/contents/ui/VeltOSDesktop.qml").write_text(
            "// Plasma's own\n", encoding="utf-8")
        self.assertEqual(self.run_tool(), 1)
        self.assertFalse((self.applets / "org.kde.desktopcontainment").exists())

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
                elif "add" in change:
                    self.assertTrue((PKG / "plasma-overrides/files" / change["add"]).is_file())
                else:
                    self.assertNotEqual(change["old"], change["new"])


if __name__ == "__main__":
    unittest.main()
