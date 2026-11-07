"""Texts the running VeltOS shows never name Windows (product owner,
2026-11-07): the apps' texts (strings.py), Settings' catalogue, application
launchers, the plasmoids' and KWin's descriptions, translations, the
plasmoids' own texts and the installer's pages. ".exe programs" and the
"Super" key are the names used instead. Code, comments and configuration
keys may still say Windows (a kwinrc group, a registry path, a file's
signature): only text a person reads is checked."""

import ast
import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKAGES = REPO / "packages"
WORD = re.compile(r"\bWindows\b")
DESKTOP_KEYS = re.compile(r"^(Name|GenericName|Comment)(\[[\w@]+\])?=(.*)$")
QML_TEXT = re.compile(r'\b(?:i18n|i18nc|i18nd|qsTr|t)\(\s*"((?:[^"\\]|\\.)*)"(?:\s*,\s*"((?:[^"\\]|\\.)*)")?')


def files(pattern):
    return [p for p in PACKAGES.rglob(pattern)
            if "tests" not in p.parts and "build-assets" not in p.parts and "__pycache__" not in p.parts]


def python_texts(path):
    """String constants of a module, without its docstrings."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node.lineno, node.value


class NoWindowsInTexts(unittest.TestCase):
    def check(self, found):
        self.assertEqual(found, [], "texts that name Windows:\n" + "\n".join(found))

    def test_app_texts_and_settings_catalogue(self):
        found = []
        for path in files("strings.py") + files("catalog.py"):
            for line, text in python_texts(path):
                if WORD.search(text):
                    found.append(f"{path.relative_to(REPO)}:{line}: {text[:80]}")
        self.check(found)

    def test_launchers(self):
        found = []
        for path in files("*.desktop"):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                match = DESKTOP_KEYS.match(line)
                if match and WORD.search(match.group(3)):
                    found.append(f"{path.relative_to(REPO)}:{number}: {line[:80]}")
        self.check(found)

    def test_plasmoid_and_kwin_descriptions(self):
        found = []
        for path in files("metadata.json"):
            plugin = json.loads(path.read_text(encoding="utf-8")).get("KPlugin", {})
            for key, value in plugin.items():
                if (key.startswith("Name") or key.startswith("Description")) and isinstance(value, str) \
                        and WORD.search(value):
                    found.append(f"{path.relative_to(REPO)}: {key}: {value[:80]}")
        self.check(found)

    def test_translations(self):
        found = []
        for path in files("*.po"):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.startswith(("msgid ", "msgstr ")) and WORD.search(line):
                    found.append(f"{path.relative_to(REPO)}:{number}: {line[:80]}")
        self.check(found)

    def test_plasmoid_and_installer_page_texts(self):
        found = []
        roots = [PACKAGES / "veltos-desktop/plasma", PACKAGES / "veltos-desktop/plasma-overrides/files",
                 PACKAGES / "calamares-settings-veltos/calamares/branding"]
        for root in roots:
            for path in root.rglob("*.qml"):
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    for match in QML_TEXT.finditer(line):
                        if any(WORD.search(text or "") for text in match.groups()):
                            found.append(f"{path.relative_to(REPO)}:{number}: {line.strip()[:80]}")
        for path in (PACKAGES / "calamares-settings-veltos/calamares/modules").glob("*.conf"):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if re.match(r"\s*(step|description|name)(\[\w+\])?:", line) and WORD.search(line):
                    found.append(f"{path.relative_to(REPO)}:{number}: {line.strip()[:80]}")
        self.check(found)

    def test_the_checks_see_such_a_text(self):
        # The patterns themselves: a Windows text would be found.
        self.assertTrue(QML_TEXT.search('text: i18n("Ask (Windows + C)")'))
        self.assertTrue(WORD.search(QML_TEXT.search('t("Windows programs", "x")').group(1)))
        self.assertTrue(DESKTOP_KEYS.match("Comment[tr]=Windows programları"))
        self.assertFalse(WORD.search("Snap windows"))     # app windows, not the product


if __name__ == "__main__":
    unittest.main()
