"""Personalization > Taskbar (taskbar.py): what is read from and written to
Plasma's taskbar through plasmashell's scripting interface (fake runner;
no Plasma needed)."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_settings import catalog, strings, taskbar  # noqa: E402


class Runner:
    def __init__(self, reply=(0, "")):
        self.reply = reply
        self.calls = []

    def __call__(self, command, timeout=20):
        self.calls.append(command)
        return self.reply


class TaskbarTests(unittest.TestCase):
    def test_reads_the_running_taskbar(self):
        found = {"autoHide": True, "search": 1, "taskView": False, "showDesktop": True, "alignment": "left",
                 "badges": False, "combine": "never",
                 "tray": {"org.kde.plasma.clipboard": False, "org.kde.plasma.keyboardlayout": True},
                 "trayKnown": ["org.kde.plasma.clipboard", "org.kde.plasma.keyboardlayout"]}
        runner = Runner((0, "js: something\n" + json.dumps(found) + "\n"))
        state = taskbar.Taskbar(runner).state("tr")
        command = runner.calls[0]
        self.assertEqual(command[:4], ["qdbus6", "org.kde.plasmashell", "/PlasmaShell",
                                       "org.kde.PlasmaShell.evaluateScript"])
        self.assertIn("print(JSON.stringify(state));", command[4])
        self.assertTrue(state["available"])
        self.assertEqual((state["search"], state["taskView"], state["alignment"], state["combine"]),
                         (1, False, "left", "never"))
        self.assertTrue(state["autoHide"])
        self.assertFalse(state["badges"])
        # Only the tray icons this taskbar knows, with Windows' names.
        self.assertEqual([(i["id"], i["title"], i["shown"]) for i in state["trayItems"]],
                         [("org.kde.plasma.keyboardlayout", "Giriş göstergesi", True),
                          ("org.kde.plasma.clipboard", "Pano", False)])

    def test_without_plasma_defaults_and_unavailable(self):
        state = taskbar.Taskbar(Runner((1, ""))).state()
        self.assertFalse(state["available"])
        self.assertEqual(state["search"], 3)
        self.assertEqual(state["alignment"], "center")
        self.assertEqual(len(state["trayItems"]), len(taskbar.TRAY_ITEMS))
        # Nonsense from the script is ignored.
        state = taskbar.Taskbar(Runner((0, json.dumps({"search": 9, "alignment": "middle"})))).state()
        self.assertEqual((state["search"], state["alignment"]), (3, "center"))

    def test_changes_become_scripts(self):
        runner = Runner()
        bar = taskbar.Taskbar(runner)
        self.assertTrue(bar.set("search", 2))
        self.assertIn("w.writeConfig('mode', 2);", runner.calls[-1][4])
        self.assertTrue(bar.set("alignment", "left"))
        self.assertIn("spacer.writeConfig('expanding', \"left\" === 'center');", runner.calls[-1][4])
        self.assertTrue(bar.set("autoHide", True))
        self.assertIn("panel.hiding = true ? 'autohide' : 'none';", runner.calls[-1][4])
        self.assertTrue(bar.set("combine", "never"))
        self.assertIn("w.writeConfig('groupingStrategy', \"never\" === 'never' ? 0 : 1);", runner.calls[-1][4])
        self.assertTrue(bar.set("showDesktop", False))
        self.assertIn("w.writeConfig('enabled', false);", runner.calls[-1][4])
        self.assertTrue(bar.set("aiButton", False))
        self.assertIn("panel.widgets('org.veltos.aibutton')", runner.calls[-1][4])
        self.assertIn("w.writeConfig('shown', false);", runner.calls[-1][4])
        self.assertFalse(bar.set("aiButton", "no"))
        self.assertTrue(bar.set_tray_item("org.kde.plasma.clipboard", True))
        self.assertIn('var id = "org.kde.plasma.clipboard";', runner.calls[-1][4])
        count = len(runner.calls)
        # Values that are not settings never reach Plasma.
        self.assertFalse(bar.set("search", 7))
        self.assertFalse(bar.set("search", True))
        self.assertFalse(bar.set("alignment", "'); evil(); ('"))
        self.assertFalse(bar.set("autoHide", "yes"))
        self.assertFalse(bar.set("unknown", 1))
        self.assertFalse(bar.set_tray_item("org.kde.plasma.evil", True))
        self.assertEqual(len(runner.calls), count)

    def test_page_is_in_personalization_and_has_texts(self):
        self.assertEqual(catalog.page_for_module("taskbar"), "taskbar")
        items = [item["page"] for item in catalog.page("personalization")["items"]]
        self.assertIn("taskbar", items)
        qml = (Path(__file__).resolve().parent.parent / "veltos_settings/qml/TaskbarPage.qml").read_text(encoding="utf-8")
        import re
        for key in set(re.findall(r'backend\.text\("([a-z_]+)"\)', qml)):
            for lang in ("en", "tr"):
                self.assertTrue(strings.text(lang, key), key)


if __name__ == "__main__":
    unittest.main()
