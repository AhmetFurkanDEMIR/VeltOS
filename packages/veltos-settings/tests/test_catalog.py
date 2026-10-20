"""Tests for the settings catalogue and texts."""

import re
import string
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_settings import catalog, strings  # noqa: E402

QML = Path(__file__).resolve().parent.parent / "veltos_settings" / "qml"


class CatalogTests(unittest.TestCase):
    def all_items(self):
        for page in catalog.PAGES:
            for item in page["items"]:
                yield page, item

    def test_every_item_does_exactly_one_thing(self):
        for _page, item in self.all_items():
            targets = [key for key in ("kcm", "page", "action") if item.get(key)]
            self.assertEqual(len(targets), 1, item["id"])
            self.assertNotIn("kcm", item, item["id"])           # no KDE settings window, ever
            if item.get("page"):
                self.assertIn(item["page"], catalog.BUILTIN_PAGES, item["id"])
            if item.get("action"):
                self.assertIn(item["action"], catalog.ACTIONS, item["id"])

    def test_no_page_opens_kde_settings(self):
        for path in QML.glob("*.qml"):
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"\bkcm_\w+|kcmshell|systemsettings|openModule", text), path.name)

    def test_every_builtin_page_has_a_component(self):
        main = (QML / "Main.qml").read_text(encoding="utf-8")
        for page in catalog.BUILTIN_PAGES:
            if page != "home":
                self.assertIn(f'"{page}":', main, page)

    def test_icons_are_monochrome_line_icons(self):
        for page in catalog.PAGES:
            self.assertTrue(page["icon"].endswith("-symbolic"), page["id"])
        for _page, item in self.all_items():
            self.assertTrue(item["icon"].endswith("-symbolic"), item["id"])
        for path in QML.glob("*Page.qml"):
            for icon in re.findall(r'\bicon: "([^"]+)"', path.read_text(encoding="utf-8")):
                self.assertTrue(icon.endswith("-symbolic"), f"{path.name}: {icon}")

    def test_texts_in_both_languages(self):
        for page in catalog.PAGES:
            self.assertEqual(len(page["title"]), 2)
            self.assertTrue(all(page["title"]))
        for _page, item in self.all_items():
            for key in ("title", "desc"):
                self.assertEqual(len(item[key]), 2, item["id"])
                self.assertTrue(all(item[key]), item["id"])
                for text in item[key]:
                    self.assertNotIn("debian", text.lower())
                    self.assertNotIn("kde", text.lower().split())

    def test_ids_unique(self):
        page_ids = [p["id"] for p in catalog.PAGES]
        self.assertEqual(len(page_ids), len(set(page_ids)))
        item_ids = [item["id"] for _page, item in self.all_items()]
        self.assertEqual(len(item_ids), len(set(item_ids)))

    def test_localized_pages(self):
        pages = catalog.localized_pages("tr")
        self.assertEqual(pages[0]["title"], "Giriş")
        system = next(p for p in pages if p["id"] == "system")
        self.assertEqual(system["items"][0]["title"], "Ekran")
        self.assertEqual(catalog.localized_pages("de")[0]["title"], "Home")

    def test_search_finds_windows_words_in_both_languages(self):
        titles = [r["title"] for r in catalog.search("wifi", "en")]
        self.assertIn("Wi-Fi", titles)
        self.assertTrue(any(r["id"] == "otherusers" for r in catalog.search("kullanıcı ekle", "tr")))
        self.assertTrue(any(r["id"] == "region" for r in catalog.search("turkce", "tr")))
        self.assertTrue(any(r["id"] == "sound" for r in catalog.search("HOPARLÖR", "tr")))
        self.assertTrue(any(r["id"] == "about" for r in catalog.search("bilgisayar adı", "tr")))
        result = catalog.search("ekran", "tr")[0]
        self.assertIn("pageTitle", result)
        self.assertEqual(catalog.search("   ", "en"), [])
        self.assertEqual(catalog.search("xyzzy", "en"), [])


class StringsTests(unittest.TestCase):
    def test_both_languages_have_the_same_placeholders(self):
        for key, (english, turkish) in strings.TEXTS.items():
            fields = lambda text: {f for _, f, _, _ in string.Formatter().parse(text) if f}
            self.assertEqual(fields(english), fields(turkish), key)

    def test_language_detection(self):
        self.assertEqual(strings.language({"LANG": "tr_TR.UTF-8"}), "tr")
        self.assertEqual(strings.language({"LANG": "en_GB.UTF-8"}), "en")
        self.assertEqual(strings.text("tr", "app_title"), "Ayarlar")
        self.assertEqual(strings.text("en", "home_welcome", name="Velt"), "Welcome, Velt")


if __name__ == "__main__":
    unittest.main()
