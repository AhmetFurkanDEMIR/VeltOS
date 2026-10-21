"""Checks VeltOS' LibreOffice configuration layer against the schema and
data of the installed LibreOffice (libreoffice-common is a Build-Depends):
every component, group and property must exist, the set entries must be
ones LibreOffice defines (toolbar modes, document factories), and the
values must name things LibreOffice has (the "Tabbed" mode, the Word/
Excel/PowerPoint filters, the Colibre icons). A LibreOffice update that
renames any of them fails the package build instead of silently dropping
the setting."""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

OOR = "{http://openoffice.org/2001/registry}"
HERE = Path(__file__).resolve().parent.parent
LAYER = HERE / "registry" / "veltos-office.xcd"
LO = Path("/usr/lib/libreoffice")


def registry_files():
    """LibreOffice's own .xcd files (main.xcd may only be in .registry when
    libreoffice-common's maintainer script has not linked it yet)."""
    files = {}
    for folder in (LO / "share" / ".registry", LO / "share" / "registry"):
        for path in sorted(folder.glob("*.xcd")):
            if path.name != LAYER.name and path.exists():
                files.setdefault(path.name, path)
    return list(files.values())


def settings(element, path=()):
    """(path, value) for every prop under element, path = node names."""
    for child in element:
        if child.tag == "node":
            yield from settings(child, path + (child.get(f"{OOR}name"),))
        elif child.tag == "prop":
            value = child.find("value")
            yield path + (child.get(f"{OOR}name"),), None if value is None else value.text


@unittest.skipUnless(registry_files(), "needs LibreOffice's registry (libreoffice-common, Build-Depends)")
class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roots = [ET.parse(path).getroot() for path in registry_files()]
        cls.layer = ET.parse(LAYER).getroot()
        cls.schemas = {}
        for root in cls.roots:
            for schema in root.iter(f"{OOR}component-schema"):
                cls.schemas[(schema.get(f"{OOR}package"), schema.get(f"{OOR}name"))] = schema

    def data_nodes(self, package, component):
        for root in self.roots:
            for data in root.iter(f"{OOR}component-data"):
                if data.get(f"{OOR}package") == package and data.get(f"{OOR}name") == component:
                    yield data

    def template(self, schema, set_element):
        name = set_element.get(f"{OOR}node-type")
        owner = set_element.get(f"{OOR}component")
        if owner:
            package, _, component = owner.rpartition(".")
            schema = self.schemas[(package, component)]
        for group in schema.find("templates"):
            if group.get(f"{OOR}name") == name:
                return group
        self.fail(f"template {name} missing")

    def resolve(self, package, component, path):
        """The schema element of path; asserts each step exists."""
        schema = self.schemas.get((package, component))
        self.assertIsNotNone(schema, f"{package}.{component} is not a LibreOffice component")
        current = schema.find("component")
        for step in path[:-1]:
            if current.tag == "set":
                current = self.template(schema, current)
                continue
            if current.tag == "node-ref":
                current = self.template(schema, current)
            match = [c for c in current if c.get(f"{OOR}name") == step and c.tag in ("group", "set", "node-ref")]
            self.assertTrue(match, f"{package}.{component}: no {step} in {'/'.join(path)}")
            current = match[0]
        if current.tag in ("set", "node-ref"):
            current = self.template(schema, current)
        props = [c for c in current if c.tag == "prop" and c.get(f"{OOR}name") == path[-1]]
        if not props and current.get(f"{OOR}extensible") == "true":
            # Extensible groups (VCL's DefaultFonts) declare their
            # properties in the data: the property must be there.
            self.assertTrue(self.data_prop_exists(package, component, path),
                            f"{package}.{component}: no property {'/'.join(path)} in the data")
            return None
        self.assertTrue(props, f"{package}.{component}: no property {'/'.join(path)}")
        return props[0]

    def data_prop_exists(self, package, component, path):
        for data in self.data_nodes(package, component):
            current = [data]
            for step in path[:-1]:
                current = [c for e in current for c in e if c.tag == "node" and c.get(f"{OOR}name") == step]
            if any(c.tag == "prop" and c.get(f"{OOR}name") == path[-1] for e in current for c in e):
                return True
        return False

    def test_every_setting_exists_in_the_schema(self):
        count = 0
        for data in self.layer.iter(f"{OOR}component-data"):
            package, component = data.get(f"{OOR}package"), data.get(f"{OOR}name")
            for path, value in settings(data):
                prop = self.resolve(package, component, path)
                kind = prop.get(f"{OOR}type") if prop is not None else None
                if kind == "xs:boolean":
                    self.assertIn(value, ("true", "false"), path)
                count += 1
        self.assertGreaterEqual(count, 21)

    def entry_exists(self, package, component, path):
        """Whether LibreOffice's data has the set entry at path."""
        for data in self.data_nodes(package, component):
            current = [data]
            for step in path:
                current = [c for e in current for c in e if c.tag == "node" and c.get(f"{OOR}name") == step]
            if current:
                return True
        return False

    def modes(self, app):
        """{CommandArg: HasNotebookbar} of an application's toolbar modes."""
        found = {}
        for data in self.data_nodes("org.openoffice.Office.UI", "ToolbarMode"):
            for apps in data.iter("node"):
                if apps.get(f"{OOR}name") != "Applications":
                    continue
                for node in apps:
                    if node.get(f"{OOR}name") != app or node.find("node") is None:
                        continue
                    for mode in node.find("node"):
                        values = dict((path[-1], value) for path, value in settings(mode))
                        if "CommandArg" in values:
                            found[values["CommandArg"]] = values.get("HasNotebookbar") == "true"
        return found

    def test_set_entries_and_values_are_known(self):
        # "Active" is a mode's CommandArg (sfx2 SfxNotebookBar::IsActive):
        # the first try named the node ("Tabbed") and LibreOffice kept its
        # toolbars (VM, 2026-10-21).
        for data in self.layer.iter(f"{OOR}component-data"):
            if data.get(f"{OOR}name") == "ToolbarMode":
                active = {path[1]: value for path, value in settings(data)}
        self.assertEqual(set(active), {"Writer", "Calc", "Impress"})
        for app, value in active.items():
            self.assertTrue(self.modes(app).get(value), f"{app}: {value} is not a mode with the notebook bar")
        filters = {}
        for data in self.layer.iter(f"{OOR}component-data"):
            if data.get(f"{OOR}name") == "Setup":
                for path, value in settings(data):
                    filters[path[2]] = value
        self.assertEqual(len(filters), 3)
        for factory, name in filters.items():
            self.assertTrue(self.entry_exists("org.openoffice", "Setup", ("Office", "Factories", factory)), factory)
            self.assertTrue(self.entry_exists("org.openoffice.TypeDetection", "Filter", ("Filters", name)), name)

    def test_icon_set_is_installed(self):
        self.assertTrue((Path("/usr/share/libreoffice/share/config") / "images_colibre.zip").exists()
                        or (LO / "share" / "config" / "images_colibre.zip").exists())


class LayerTests(unittest.TestCase):
    def test_layer_is_well_formed(self):
        root = ET.parse(LAYER).getroot()
        self.assertEqual(root.tag, f"{OOR}data")
        self.assertEqual(root.find("dependency").get("file"), "main")


if __name__ == "__main__":
    unittest.main()
