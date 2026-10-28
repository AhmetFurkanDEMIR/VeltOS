"""MSI's msi-ec for Keyboard Lighting (driver.py): the firmware version from
the EC's debug file, what the pinned source supports (tools/support-table.py
on upstream/msi-ec.c, present in package builds) and the DKMS steps, with a
stand-in for dkms and modprobe."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from veltos_msi_ec import driver  # noqa: E402

spec = importlib.util.spec_from_file_location("support_table", HERE / "tools/support-table.py")
support_table = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support_table)
UPSTREAM = HERE / "upstream/msi-ec.c"


class FakeTools:
    """dkms and modprobe: `dkms status` lists what was added."""

    def __init__(self, modprobe_out="", modprobe_code=0, registered=()):
        self.calls, self.added = [], list(registered)
        self.modprobe_out, self.modprobe_code = modprobe_out, modprobe_code

    def __call__(self, command, timeout=None):
        self.calls.append(command)
        if command[:2] == ["dkms", "status"]:
            return 0, "".join(f"msi-ec/{v}, 6.12.113+deb13-amd64, x86_64: installed\n" for v in self.added)
        if command[:2] == ["dkms", "add"]:
            self.added.append(command[command.index("-v") + 1])
        if command[:2] == ["dkms", "remove"]:
            self.added.remove(command[2].split("/")[1])
        if command == ["modprobe", "msi_ec"]:
            return self.modprobe_code, self.modprobe_out
        return 0, ""


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.source = self.root / "share/src"
        self.source.mkdir(parents=True)
        (self.source / "msi-ec.c").write_text("/* driver */\n")
        conf = (HERE / "data/dkms.conf.in").read_text().replace("@VERSION@", "0.13+git20260809.d7fbbd8")
        (self.source / "dkms.conf").write_text(conf)
        self.paths = {"source": self.source, "usr_src": self.root / "usr/src",
                      "modules_load": self.root / "etc/modules-load.d/veltos-msi-ec.conf",
                      "led": self.root / "leds/kbd_backlight"}

    def test_firmware_from_the_ec(self):
        io = self.root / "io"
        data = bytearray(256)
        data[0xA0:0xAC] = b"1582EMS1.107"
        io.write_bytes(bytes(data))
        self.assertEqual(driver.firmware(io, self.root / "none"), "1582EMS1.107")
        io.write_bytes(bytes(256))                       # not an MSI EC
        self.assertEqual(driver.firmware(io, self.root / "none"), "")
        self.assertEqual(driver.firmware(self.root / "missing", self.root / "none"), "")
        platform = self.root / "platform"
        platform.mkdir()
        (platform / "fw_version").write_text("1585EMS1.112\n")
        self.assertEqual(driver.firmware(self.root / "missing", platform), "1585EMS1.112")

    def test_status_of_an_msi_laptop(self):
        dmi = self.root / "dmi"
        dmi.mkdir()
        (dmi / "sys_vendor").write_text("Micro-Star International Co., Ltd.\n")
        (dmi / "product_name").write_text("Katana GF66 11UC\n")
        table = self.root / "support.json"
        table.write_text(json.dumps({"1582EMS1.107": {"keyboard": True, "models": "Katana GF66 11UC / 11UD"}}))
        io = self.root / "io"
        io.write_bytes(bytes(0xA0) + b"1582EMS1.107" + bytes(84))
        state = driver.status(io, self.root / "none", self.paths["led"], dmi, table, self.paths["modules_load"])
        self.assertTrue(state["msi"])
        self.assertEqual(state["model"], "Katana GF66 11UC")
        self.assertEqual(state["support"], {"known": True, "keyboard": True, "models": "Katana GF66 11UC / 11UD"})
        self.assertFalse(state["installed"] or state["running"] or state["light"])
        (dmi / "sys_vendor").write_text("LENOVO\n")
        self.assertFalse(driver.status(io, self.root / "none", self.paths["led"], dmi, table)["msi"])
        self.assertEqual(driver.support("", table)["known"], False)

    def test_install_steps(self):
        tools = FakeTools(registered=["0.12"])
        self.paths["led"].mkdir(parents=True)          # the module made the keyboard light
        result = driver.install(tools, kernel="6.12.113+deb13-amd64", **self.paths)
        self.assertEqual(result["reason"], "")
        self.assertTrue(result["ok"])
        calls = [" ".join(c) for c in tools.calls]
        self.assertIn("dkms remove msi-ec/0.12 --all", calls)
        self.assertIn("dkms add -m msi-ec -v 0.13+git20260809.d7fbbd8", calls)
        self.assertIn("dkms install -m msi-ec -v 0.13+git20260809.d7fbbd8 -k 6.12.113+deb13-amd64 --force", calls)
        self.assertLess(calls.index("modprobe -r msi_ec"), calls.index("modprobe msi_ec"))
        self.assertTrue((self.paths["usr_src"] / "msi-ec-0.13+git20260809.d7fbbd8/msi-ec.c").exists())
        self.assertIn("msi-ec", self.paths["modules_load"].read_text().splitlines())
        # Run again: nothing is added twice.
        tools.calls.clear()
        driver.install(tools, kernel="6.12.113+deb13-amd64", **self.paths)
        self.assertNotIn(["dkms", "add", "-m", "msi-ec", "-v", "0.13+git20260809.d7fbbd8"], tools.calls)

    def test_install_outcomes(self):
        cases = [("modprobe: ERROR: could not insert 'msi_ec': Key was rejected by service", 1, "key"),
                 ("modprobe: ERROR: could not insert 'msi_ec': Operation not supported", 1, "unsupported"),
                 ("modprobe: ERROR: could not insert 'msi_ec': No such device", 1, "load"),
                 ("", 0, "nolight")]
        for out, code, reason in cases:
            tools = FakeTools(out, code)
            result = driver.install(tools, kernel="k", **self.paths)
            self.assertEqual(result["reason"], reason, out)
            self.assertEqual(result["ok"], reason == "nolight")
            # Kept where it runs or will run after the Secure Boot key;
            # taken out again where it cannot run (the kernel's own comes back).
            kept = reason in ("key", "nolight")
            self.assertEqual(self.paths["modules_load"].exists(), kept, reason)
            self.assertEqual(tools.added != [], kept, reason)

        class NoDkms(FakeTools):
            def __call__(self, command, timeout=None):
                return (127, "dkms: not found") if command[0] == "dkms" else super().__call__(command)
        self.assertEqual(driver.install(NoDkms(), kernel="k", **self.paths)["reason"], "nodkms")

    def test_remove_and_upgrade(self):
        tools = FakeTools(registered=["0.13+git20260809.d7fbbd8"])
        self.assertEqual(driver.upgrade(tools, **self.paths)["log"], "")        # never installed here
        self.paths["modules_load"].parent.mkdir(parents=True)
        self.paths["modules_load"].write_text("msi-ec\n")
        self.assertEqual(driver.upgrade(tools, **self.paths)["log"], "")        # this version is there
        driver.remove(tools, self.paths["usr_src"], self.paths["modules_load"])
        self.assertEqual(tools.added, [])
        self.assertFalse(self.paths["modules_load"].exists())
        self.assertEqual(tools.calls[-1], ["modprobe", "msi_ec"])               # the kernel's own again

    def test_version_and_headers(self):
        self.assertEqual(driver.version(self.source), "0.13+git20260809.d7fbbd8")
        self.assertEqual(driver.headers_package("6.12.113+deb13-amd64"), "linux-headers-6.12.113+deb13-amd64")
        pin = json.loads((HERE / "upstream.json").read_text())
        self.assertTrue(pin["version"].startswith("0.13+git"))

    @unittest.skipUnless(UPSTREAM.exists(), "needs the fetched upstream source (package builds)")
    def test_support_table_from_the_pinned_source(self):
        table = support_table.table(UPSTREAM.read_text(encoding="utf-8"))
        self.assertGreater(len(table), 300)
        self.assertTrue(table["1582EMS1.107"]["keyboard"])          # Katana GF66 11UC / 11UD
        self.assertIn("Katana", table["1582EMS1.107"]["models"])
        self.assertTrue(table["1585EMS1.112"]["keyboard"])          # Katana 15 B13VGK
        self.assertFalse(table["1587EMS1.102"]["keyboard"])         # Katana 15 HX B14W: RGB, not in msi-ec

    def test_support_table_refuses_a_changed_source(self):
        with self.assertRaises(SystemExit):
            support_table.table("static int nothing;")


if __name__ == "__main__":
    unittest.main()
