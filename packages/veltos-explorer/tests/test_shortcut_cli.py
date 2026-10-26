"""CLI used by Start and Search to create shortcuts for recent documents."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from veltos_explorer import shortcut_cli


class ShortcutCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.desktop = self.home / "Desktop"
        self.desktop.mkdir()
        self.source = self.home / "Notes & plans.txt"
        self.source.write_text("shortcut target", encoding="utf-8")
        self.notifications = []

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, argument):
        return shortcut_cli.run(
            ["veltos-explorer", "--create-shortcut", argument],
            desktop=self.desktop,
            notifier=lambda *notification: self.notifications.append(notification),
        )

    def test_file_url_creates_non_overwriting_symlink_and_notifies(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(self.run_cli(self.source.as_uri()), 0)

        shortcut = self.desktop / "Notes & plans - Shortcut.txt"
        self.assertTrue(shortcut.is_symlink())
        self.assertEqual(shortcut.resolve(), self.source)
        self.assertIn(str(shortcut), output.getvalue())
        self.assertEqual(self.notifications, [
            ("File Explorer", "Shortcut created on the desktop.")
        ])

    def test_repeated_request_uses_a_unique_name(self):
        self.assertEqual(self.run_cli(str(self.source)), 0)
        self.assertEqual(self.run_cli(str(self.source)), 0)

        shortcuts = sorted(self.desktop.glob("* - Shortcut*.txt"))
        self.assertEqual(len(shortcuts), 2)
        self.assertTrue(all(path.is_symlink() and path.resolve() == self.source for path in shortcuts))

    def test_non_local_url_is_rejected_and_reported(self):
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(self.run_cli("https://example.invalid/notes.txt"), 1)

        self.assertIn("Only local files and folders", error.getvalue())
        self.assertEqual(list(self.desktop.iterdir()), [])
        self.assertEqual(len(self.notifications), 1)
        self.assertTrue(self.notifications[0][2])

    def test_missing_source_is_reported(self):
        self.assertEqual(self.run_cli(str(self.home / "missing.txt")), 1)
        self.assertEqual(list(self.desktop.iterdir()), [])
        self.assertEqual(len(self.notifications), 1)
        self.assertTrue(self.notifications[0][2])

    def test_argument_count_is_validated(self):
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(shortcut_cli.run(["veltos-explorer", "--create-shortcut"]), 2)
        self.assertIn("Usage:", error.getvalue())


if __name__ == "__main__":
    unittest.main()
