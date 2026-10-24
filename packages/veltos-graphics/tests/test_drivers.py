"""Which driver each card gets: the plan for NVIDIA, AMD, Intel and virtual
cards, nvidia-detect's answer, apt's candidate and Secure Boot."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from veltos_graphics import drivers, gpus  # noqa: E402
import samples  # noqa: E402

INTEL, NVIDIA = gpus.parse_lspci(samples.LSPCI_NVIDIA_INTEL)
(AMD,) = gpus.parse_lspci(samples.LSPCI_AMD)
(VIRTIO,) = gpus.parse_lspci(samples.LSPCI_VIRTIO)
OPEN_STACK = {"firmware-amd-graphics": "20250410-2", "firmware-intel-graphics": "20250410-2",
              "mesa-vulkan-drivers": "25.0.7-2+deb13u1", "libgl1-mesa-dri": "25.0.7-2+deb13u1"}


def runner_for(text, code=0):
    return lambda command, timeout=60: (code, text)


class PlanTests(unittest.TestCase):
    def test_nvidia_without_driver_offers_install_with_headers(self):
        plan = drivers.plan(NVIDIA, {}, {"nouveau"})
        self.assertEqual(plan["state"], "available")
        self.assertEqual(plan["action"], "install")
        self.assertEqual(plan["packages"], ["nvidia-driver", "linux-headers-amd64"])
        self.assertEqual(plan["driver"], "nouveau")

    def test_nvidia_detect_recommendation_is_used(self):
        plan = drivers.plan(NVIDIA, {}, set(), "nvidia-tesla-535-driver")
        self.assertEqual(plan["packages"], ["nvidia-tesla-535-driver", "linux-headers-amd64"])

    def test_nvidia_legacy_card_is_unsupported(self):
        plan = drivers.plan(NVIDIA, {}, set(), "unsupported")
        self.assertEqual((plan["state"], plan["action"]), ("unsupported", ""))

    def test_nvidia_driver_installed_waits_for_restart(self):
        plan = drivers.plan(NVIDIA, {"nvidia-driver": "550.163.01-2"}, {"nouveau"})
        self.assertEqual((plan["state"], plan["action"]), ("restart", ""))
        self.assertTrue(plan["openDriver"])

    def test_nvidia_driver_in_use(self):
        card = dict(NVIDIA, driver="nvidia")
        plan = drivers.plan(card, {"nvidia-driver": "550.163.01-2"}, {"nvidia", "nvidia_drm"})
        self.assertEqual((plan["state"], plan["action"]), ("proprietary", "update"))
        self.assertEqual(plan["packages"], ["nvidia-driver"])
        self.assertEqual(plan["version"], "550.163.01-2")
        self.assertEqual(plan["driver"], "nvidia")

    def test_amd_and_intel_missing_parts(self):
        installed = dict(OPEN_STACK)
        del installed["firmware-amd-graphics"]
        plan = drivers.plan(AMD, installed, {"amdgpu"})
        self.assertEqual((plan["state"], plan["action"]), ("missing", "install"))
        self.assertEqual(plan["packages"], ["firmware-amd-graphics"])
        self.assertEqual(drivers.plan(INTEL, installed, {"i915"})["state"], "ready")

    def test_complete_open_stack_offers_updates(self):
        plan = drivers.plan(AMD, OPEN_STACK, {"amdgpu"})
        self.assertEqual((plan["state"], plan["action"]), ("ready", "update"))
        self.assertEqual(plan["packages"], ["firmware-amd-graphics", "mesa-vulkan-drivers", "libgl1-mesa-dri"])

    def test_virtual_and_other_cards(self):
        self.assertEqual(drivers.plan(VIRTIO, OPEN_STACK, set())["state"], "virtual")
        self.assertEqual(drivers.plan(dict(AMD, kind="other"), {}, set())["state"], "unknown")

    def test_open_driver_packages(self):
        listing = "".join(f"{name}\t{arch}\t{status}\n" for name, arch, status in (
            ("nvidia-driver", "amd64", "ii "), ("nvidia-detect", "amd64", "ii "), ("libnvidia-glcore", "amd64", "ii "),
            ("libnvidia-glcore", "i386", "ii "), ("nvidia-kernel-common", "amd64", "rc "),
            ("glx-alternative-nvidia", "amd64", "ii "), ("xserver-xorg-video-nvidia", "amd64", "ii "),
            ("libcuda1", "i386", "ii "), ("firmware-nvidia-graphics", "all", "ii "), ("mesa-vulkan-drivers", "amd64", "ii ")))
        self.assertEqual(drivers.open_driver_packages(runner=runner_for(listing)),
                         ["nvidia-driver:amd64", "libnvidia-glcore:amd64", "libnvidia-glcore:i386",
                          "glx-alternative-nvidia:amd64", "xserver-xorg-video-nvidia:amd64", "libcuda1:i386"])

    def test_native_arch(self):
        self.assertEqual(drivers.native_arch(runner=runner_for("amd64\n")), "amd64")
        self.assertEqual(drivers.native_arch(runner=runner_for("", code=1)), "amd64")


class CommandTests(unittest.TestCase):
    def test_installed_packages(self):
        out = ("nvidia-driver\tii \t550.163.01-2\nmesa-vulkan-drivers:amd64\tii \t25.0.7-2+deb13u1\n"
               "nvidia-detect\trc \t550.163.01-2\n")
        self.assertEqual(drivers.installed_packages(runner=runner_for(out)),
                         {"nvidia-driver": "550.163.01-2", "mesa-vulkan-drivers": "25.0.7-2+deb13u1"})

    def test_loaded_modules(self):
        path = Path(tempfile.mkdtemp()) / "modules"
        path.write_text("nvidia_drm 139264 4 - Live 0x0\nnvidia 54308864 50 nvidia_drm, Live 0x0\n")
        self.assertEqual(drivers.loaded_modules(path), {"nvidia_drm", "nvidia"})
        self.assertEqual(drivers.loaded_modules(path.with_name("missing")), set())

    def test_nvidia_detect(self):
        with mock.patch.object(drivers.shutil, "which", return_value="/usr/bin/nvidia-detect"):
            self.assertEqual(drivers.nvidia_detect(runner=runner_for(samples.NVIDIA_DETECT_CURRENT)),
                             "nvidia-driver")
            self.assertEqual(drivers.nvidia_detect(runner=runner_for(samples.NVIDIA_DETECT_LEGACY)),
                             "unsupported")
        with mock.patch.object(drivers.shutil, "which", return_value=None):
            self.assertEqual(drivers.nvidia_detect(runner=runner_for(samples.NVIDIA_DETECT_CURRENT)), "")

    def test_available(self):
        self.assertTrue(drivers.available("nvidia-driver", runner=runner_for(samples.APT_POLICY_FOUND)))
        self.assertFalse(drivers.available("nvidia-legacy-390xx-driver", runner=runner_for(samples.APT_POLICY_NONE)))
        self.assertFalse(drivers.available("x", runner=runner_for("")))

    def test_outdated(self):
        self.assertEqual(drivers.outdated(["mesa-vulkan-drivers", "libgl1-mesa-dri", "firmware-amd-graphics", "x"],
                                          runner=runner_for(samples.APT_POLICY_UPDATES)),
                         ["mesa-vulkan-drivers"])
        self.assertEqual(drivers.outdated([], runner=runner_for(samples.APT_POLICY_UPDATES)), [])

    def test_secure_boot_and_key(self):
        key = Path(tempfile.mkdtemp()) / "mok.pub"
        with mock.patch.object(drivers.shutil, "which", return_value="/usr/bin/mokutil"):
            self.assertTrue(drivers.secure_boot(runner=runner_for("SecureBoot enabled\n")))
            self.assertFalse(drivers.secure_boot(runner=runner_for("SecureBoot disabled\n")))
            self.assertFalse(drivers.secure_boot(runner=runner_for("This system doesn't support Secure Boot\n")))
            # No key yet: nothing to enrol.
            self.assertTrue(drivers.key_enrolled(runner=runner_for(""), key=key))
            key.write_bytes(b"0")
            self.assertTrue(drivers.key_enrolled(runner=runner_for(f"{key} is already enrolled\n"), key=key))
            self.assertFalse(drivers.key_enrolled(runner=runner_for(f"{key} is not enrolled\n"), key=key))


if __name__ == "__main__":
    unittest.main()
