"""kwin-gpu-order: KWin draws on the processor's graphics when the PC has
NVIDIA's driver and another card (product owner, 2026-11-02: the monitor on
the processor's graphics was not seen)."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
SCRIPT = PKG / "system/kwin-gpu-order"


@unittest.skipUnless(os.name == "posix", "runs a shell script with symlinks")
class GpuOrderTests(unittest.TestCase):
    def order(self, cards, environ=None):
        """cards: [(name, driver, boot_vga)] -> what the script prints."""
        with tempfile.TemporaryDirectory() as tmp:
            drm, dev = Path(tmp, "drm"), Path(tmp, "dri")
            drm.mkdir()
            dev.mkdir()
            for name, driver, boot in cards:
                device = Path(tmp, "pci", name)
                (device.parent / "drivers" / driver).mkdir(parents=True, exist_ok=True)
                device.mkdir(parents=True)
                (device / "driver").symlink_to(device.parent / "drivers" / driver)
                (device / "boot_vga").write_text(f"{int(boot)}\n")
                (drm / name).mkdir()
                (drm / name / "device").symlink_to(device)
                (drm / f"{name}-HDMI-A-1").mkdir()          # connectors are ignored
                (dev / name).write_text("")
            env = dict(os.environ, VELTOS_DRM_ROOT=str(drm), VELTOS_DEV_ROOT=str(dev), **(environ or {}))
            result = subprocess.run(["sh", str(SCRIPT)], capture_output=True, text=True, env=env, check=True)
            return result.stdout.strip().replace(str(dev), "/dev/dri")

    def test_processors_graphics_first_with_nvidia(self):
        # A desktop whose firmware started on the NVIDIA card: still Intel first.
        self.assertEqual(self.order([("card0", "nvidia", True), ("card1", "i915", False)]),
                         "/dev/dri/card1:/dev/dri/card0")
        # A laptop: Intel (the panel) is card1 and the boot display.
        self.assertEqual(self.order([("card0", "nvidia", False), ("card1", "i915", True)]),
                         "/dev/dri/card1:/dev/dri/card0")
        # AMD's processor graphics, Intel's newer xe driver.
        self.assertEqual(self.order([("card1", "amdgpu", True), ("card2", "nvidia", False)]),
                         "/dev/dri/card1:/dev/dri/card2")
        self.assertEqual(self.order([("card0", "xe", False), ("card1", "nvidia", True)]),
                         "/dev/dri/card0:/dev/dri/card1")

    def test_nothing_without_two_kinds_of_card(self):
        self.assertEqual(self.order([("card0", "nvidia", True)]), "")          # NVIDIA only (MUX)
        self.assertEqual(self.order([("card0", "i915", True)]), "")
        self.assertEqual(self.order([("card0", "nouveau", True), ("card1", "i915", False)]), "")
        self.assertEqual(self.order([("card0", "virtio-pci", True)]), "")


class SessionUsesItTests(unittest.TestCase):
    def test_session_and_sign_in_screen(self):
        session = (PKG / "system/veltos-session.sh").read_text(encoding="utf-8")
        self.assertIn('veltos_gpus="$(/usr/libexec/veltos/kwin-gpu-order 2>/dev/null)"', session)
        self.assertIn('if [ -z "${KWIN_DRM_DEVICES:-}" ]; then', session)
        greeter = (PKG / "system/greeter-compositor").read_text(encoding="utf-8")
        self.assertIn('KWIN_DRM_DEVICES="$(/usr/libexec/veltos/kwin-gpu-order 2>/dev/null)"', greeter)
        self.assertLess(greeter.index("kwin-gpu-order"), greeter.index("exec kwin_wayland"))


if __name__ == "__main__":
    unittest.main()
