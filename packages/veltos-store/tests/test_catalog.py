"""VeltOS Store: catalogue, search, categories, pkcon output."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_store import catalog, packages, strings  # noqa: E402

ENTRIES = [
    {"id": "org.gimp.GIMP", "name": "GNU Image Manipulation Program", "summary": "Create images and edit photographs",
     "pkg": "gimp", "categories": ["Graphics", "2DGraphics"], "keywords": ["photo", "paint"], "icon": "file:///g.png",
     "quality": 5},
    {"id": "org.inkscape.Inkscape", "name": "Inkscape", "summary": "Vector Graphics Editor", "pkg": "inkscape",
     "categories": ["Graphics", "VectorGraphics"], "icon": "file:///i.png", "quality": 5},
    {"id": "libreoffice-writer.desktop", "name": "LibreOffice Writer", "summary": "Word processor",
     "pkg": "libreoffice-writer", "categories": ["Office", "WordProcessor"], "icon": "file:///w.png", "quality": 5},
    {"id": "supertuxkart.desktop", "name": "SuperTuxKart", "summary": "3D arcade racer", "pkg": "supertuxkart",
     "categories": ["Game", "ArcadeGame"], "icon": "file:///s.png", "quality": 4},
    {"id": "org.videolan.vlc", "name": "VLC", "summary": "VLC media player", "pkg": "vlc",
     "categories": ["AudioVideo", "Player", "Video"], "icon": "file:///v.png", "quality": 5},
    {"id": "x.bare", "name": "Bare tool", "summary": "", "pkg": "bare", "categories": [], "icon": "", "quality": 0},
    {"id": "org.gimp.GIMP", "name": "Duplicate", "pkg": "gimp", "categories": []},
]


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = catalog.Catalog(ENTRIES)

    def test_categories(self):
        self.assertEqual(catalog.category_of(["Game", "Graphics"]), "games")
        self.assertEqual(catalog.category_of(["Office"]), "productivity")
        self.assertEqual(catalog.category_of(["AudioVideo", "Player"]), "music")         # VLC
        self.assertEqual(catalog.category_of(["AudioVideo", "AudioVideoEditing", "Video"]), "photo")  # editors
        self.assertEqual(catalog.category_of(["AudioVideo", "Audio"]), "music")
        self.assertEqual(catalog.category_of([]), "utilities")
        self.assertEqual(catalog.category_title("games", "tr"), "Oyunlar")
        self.assertEqual(len(set(catalog.CATEGORY_IDS)), len(catalog.CATEGORY_IDS))

    def test_duplicate_ids_keep_the_first(self):
        self.assertEqual(len(self.catalog), 6)
        self.assertEqual(self.catalog.get("org.gimp.GIMP")["name"], "GNU Image Manipulation Program")

    def test_search_ranks_names_first(self):
        names = [e["name"] for e in self.catalog.search("ink")]
        self.assertEqual(names, ["Inkscape"])
        self.assertEqual([e["pkg"] for e in self.catalog.search("photo")], ["gimp"])     # keyword
        self.assertEqual([e["pkg"] for e in self.catalog.search("VLC")][0], "vlc")         # exact name
        self.assertEqual(self.catalog.search("  "), [])
        self.assertEqual(self.catalog.search("graphics editor"), [self.catalog.get("org.inkscape.Inkscape")])

    def test_browse_and_curated_lists(self):
        games = self.catalog.in_category(games=True)
        self.assertEqual([e["pkg"] for e in games], ["supertuxkart"])
        apps = self.catalog.in_category(games=False)
        self.assertNotIn("supertuxkart", [e["pkg"] for e in apps])
        self.assertEqual(apps[-1]["pkg"], "bare")          # the least described last
        self.assertEqual([e["pkg"] for e in self.catalog.in_category("photo")], ["gimp", "inkscape"])
        self.assertEqual([e["pkg"] for e in self.catalog.in_category("music")], ["vlc"])
        self.assertEqual([e["pkg"] for e in self.catalog.picked(["vlc", "missing", "gimp"])], ["vlc", "gimp"])

    def test_description_markup_is_sanitised(self):
        markup = ('<p onclick="x">Edit <em>photos</em></p><ul><li>One</li></ul>'
                  '<img src="http://example.org/a.png"/><a href="http://x">link</a>')
        self.assertEqual(catalog.sanitise_description(markup),
                         "<p>Edit <em>photos</em></p><ul><li>One</li></ul>link")
        self.assertEqual(catalog.sanitise_description(None), "")

    def test_catalogue_age(self):
        import tempfile
        import os
        directory = Path(tempfile.mkdtemp())
        self.assertIsNone(catalog.catalog_age_days(directory))
        f = directory / "Components-amd64.yml.gz"
        f.write_bytes(b"x")
        os.utime(f, (1000, 1000))
        self.assertAlmostEqual(catalog.catalog_age_days(directory, now=1000 + 3 * 86400), 3.0)

    def test_veltos_names_and_hidden_apps(self):
        import tempfile
        directory = Path(tempfile.mkdtemp())
        (directory / "org.kde.ark.desktop").write_text(
            "[Desktop Entry]\nName=Archive Manager\nName[tr]=Arşiv Yöneticisi\n", encoding="utf-8")
        (directory / "org.kde.dolphin.desktop").write_text("[Desktop Entry]\nName=Dolphin\nNoDisplay=true\n",
                                                           encoding="utf-8")
        entries = [{"id": "org.kde.ark", "name": "Ark", "pkg": "ark", "desktop": "org.kde.ark.desktop"},
                   {"id": "org.kde.dolphin", "name": "Dolphin", "pkg": "dolphin",
                    "desktop": "org.kde.dolphin.desktop"},
                   {"id": "vlc", "name": "VLC", "pkg": "vlc", "desktop": "vlc.desktop"}]
        self.assertEqual([e["name"] for e in catalog.apply_veltos_names(entries, "en", directory)],
                         ["Archive Manager", "VLC"])
        self.assertEqual(catalog.apply_veltos_names(entries, "tr", directory)[0]["name"], "Arşiv Yöneticisi")

    def test_protected_removals(self):
        class Result:
            def __init__(self, stdout):
                self.stdout = stdout

        dolphin = "Remv dolphin [4:25.04.3-1]\nRemv kde-plasma-desktop [5:162]\n"
        self.assertTrue(packages.removal_is_protected("dolphin", run=lambda *a, **k: Result(dolphin)))
        self.assertFalse(packages.removal_is_protected("vlc", run=lambda *a, **k: Result("Remv vlc [3.0]\n")))
        self.assertTrue(packages.removal_is_protected("veltos-store", run=lambda *a, **k: Result("")))

    def test_featured_colours(self):
        for pkg, start, end in catalog.FEATURED:
            self.assertRegex(start, r"^#[0-9A-F]{6}$")
            self.assertRegex(end, r"^#[0-9A-F]{6}$")


class PkconTests(unittest.TestCase):
    def test_progress_lines(self):
        self.assertEqual(packages.parse_progress("Percentage:\t45\n"), ("percent", 45))
        self.assertEqual(packages.parse_progress("Status: \tDownloading packages"), ("status", "downloading"))
        self.assertEqual(packages.parse_progress("Status: \tWaiting for authentication"),
                         ("status", "authorising"))
        self.assertIsNone(packages.parse_progress("Status: \tLoading cache"))
        self.assertEqual(packages.parse_progress("Fatal error: Failed to obtain authentication."),
                         ("error", "Failed to obtain authentication."))
        self.assertIsNone(packages.parse_progress("Transaction:\tInstalling"))

    def test_update_count(self):
        none = ("Transaction:\tGetting updates\nStatus: \tFinished\nResults:\n"
                "There are no updates available at this time.\n")
        self.assertEqual(packages.count_updates(none), 0)
        some = ("Status: \tFinished\nResults:\n"
                "Security     firefox-esr-128.10.0esr-1~deb13u1.amd64 (debian-security)\n"
                "Normal       tzdata-2026a-0+deb13u1.all (debian)\n")
        self.assertEqual(packages.count_updates(some), 2)
        self.assertEqual(packages.count_updates(""), 0)

    def test_installed_packages(self):
        class Result:
            stdout = "gimp\tii \nvlc:amd64\tii \nold\trc \n"

        self.assertEqual(packages.installed_packages(run=lambda *a, **k: Result()), {"gimp", "vlc"})

    def test_texts_complete(self):
        en, tr = strings.texts("en"), strings.texts("tr")
        self.assertEqual(set(en), set(tr))
        for key in ("installing", "downloading", "authorising", "removing", "updating", "waiting"):
            self.assertIn(key, en)
        self.assertEqual(strings.language({"LANGUAGE": "tr@veltos:tr"}), "tr")


if __name__ == "__main__":
    unittest.main()
