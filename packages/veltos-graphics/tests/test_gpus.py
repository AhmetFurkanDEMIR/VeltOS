"""Reading graphics cards from recorded lspci, eglinfo and vulkaninfo output."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from veltos_graphics import gpus  # noqa: E402
import samples  # noqa: E402


def runner_for(text, code=0):
    return lambda command, timeout=20: (code, text)


class LspciTests(unittest.TestCase):
    def test_laptop_with_nvidia_and_intel(self):
        cards = gpus.parse_lspci(samples.LSPCI_NVIDIA_INTEL)
        self.assertEqual([c["slot"] for c in cards], ["00:02.0", "01:00.0"])   # the USB controller is no GPU
        intel, nvidia = cards
        self.assertEqual(intel["kind"], "intel")
        self.assertEqual(intel["name"], "Intel Iris Xe Graphics")
        self.assertEqual(intel["driver"], "i915")
        self.assertEqual(intel["modules"], ["i915", "xe"])
        self.assertEqual(intel["subsystem"], "Lenovo Device")
        self.assertEqual(nvidia["kind"], "nvidia")
        self.assertEqual(nvidia["name"], "NVIDIA GeForce RTX 4060 Max-Q / Mobile")
        self.assertEqual((nvidia["vendorId"], nvidia["deviceId"]), ("10de", "28a0"))
        self.assertEqual(nvidia["vendor"], "NVIDIA Corporation")
        self.assertEqual(nvidia["driver"], "nouveau")

    def test_amd(self):
        (card,) = gpus.parse_lspci(samples.LSPCI_AMD)
        self.assertEqual(card["kind"], "amd")
        self.assertEqual(card["vendor"], "Advanced Micro Devices, Inc. [AMD/ATI]")
        self.assertEqual(card["name"], "AMD Radeon RX 6600/6600 XT/6600M")
        self.assertEqual(card["driver"], "amdgpu")

    def test_virtual_machine(self):
        (card,) = gpus.parse_lspci(samples.LSPCI_VIRTIO)
        self.assertEqual(card["kind"], "virtual")
        self.assertEqual(card["name"], "Virtio 1.0 GPU")
        self.assertEqual(card["modules"], [])

    def test_detect_handles_missing_lspci(self):
        self.assertEqual(gpus.detect(runner=runner_for("", code=1)), [])
        self.assertEqual(len(gpus.detect(runner=runner_for(samples.LSPCI_AMD))), 1)


class PropertyTests(unittest.TestCase):
    def test_renderer_reads_gbm_platform(self):
        found = gpus.renderer(runner=runner_for(samples.EGLINFO))
        self.assertEqual(found["renderer"], "llvmpipe (LLVM 19.1.7, 256 bits)")
        self.assertEqual(found["glVersion"], "4.5 (Core Profile) Mesa 25.0.7-2+deb13u1")
        self.assertEqual(found["glVendor"], "Mesa")
        self.assertEqual(found["mesa"], "25.0.7-2+deb13u1")
        self.assertEqual(gpus.renderer(runner=runner_for("", code=1)), {})

    def test_vulkan_devices(self):
        original = gpus.shutil.which
        gpus.shutil.which = lambda name: "/usr/bin/" + name
        try:
            self.assertEqual(gpus.vulkan_devices(runner=runner_for(samples.VULKANINFO)),
                             ["llvmpipe (LLVM 19.1.7, 256 bits)"])
        finally:
            gpus.shutil.which = original

    def test_video_memory_from_sysfs(self):
        root = Path(tempfile.mkdtemp())
        (root / "0000:03:00.0").mkdir()
        (root / "0000:03:00.0/mem_info_vram_total").write_text("8573157376\n")
        self.assertEqual(gpus.video_memory("03:00.0", sysfs=root), 8573157376)

    def test_video_memory_from_nvidia_smi(self):
        original = gpus.shutil.which
        gpus.shutil.which = lambda name: "/usr/bin/" + name
        try:
            memory = gpus.video_memory("01:00.0", sysfs=Path(tempfile.mkdtemp()),
                                       runner=runner_for("00000000:01:00.0, 8188\n"))
        finally:
            gpus.shutil.which = original
        self.assertEqual(memory, 8188 * 1024 * 1024)

    def test_driver_version(self):
        root = Path(tempfile.mkdtemp())
        (root / "nvidia").mkdir()
        (root / "nvidia/version").write_text("550.163.01\n")
        self.assertEqual(gpus.driver_version("nvidia", modules_dir=root), "550.163.01")
        self.assertEqual(gpus.driver_version("nouveau", modules_dir=root), "")


if __name__ == "__main__":
    unittest.main()
