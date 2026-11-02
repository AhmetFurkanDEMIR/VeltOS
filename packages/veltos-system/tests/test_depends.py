"""veltos-system names VeltOS packages only, the updater and the system's
identity among them (tests/repo checks the list against the image's
package lists)."""

import re
import unittest
from pathlib import Path

CONTROL = Path(__file__).resolve().parent.parent / "debian/control"


def depends():
    text = CONTROL.read_text(encoding="utf-8")
    field = re.search(r"^Depends:(.*?)(?=^\S)", text.split("Package: veltos-system", 1)[1], re.M | re.S).group(1)
    return [d.strip() for d in field.split(",") if d.strip() and not d.strip().startswith("${")]


class DependsTests(unittest.TestCase):
    def test_veltos_packages(self):
        names = depends()
        self.assertEqual(names, sorted(names))
        self.assertTrue(all(re.fullmatch(r"veltos-[a-z0-9-]+", n) for n in names), names)
        for needed in ("veltos-base", "veltos-update", "veltos-desktop", "veltos-settings"):
            self.assertIn(needed, names)
        self.assertNotIn("veltos-system", names)


if __name__ == "__main__":
    unittest.main()
