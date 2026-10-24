"""GPU figures from recorded DRM fdinfo, sysfs and nvidia-smi output."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_taskmanager import gpu  # noqa: E402

# /proc/PID/fdinfo/FD of a DRM file (Linux 6.12): i915 (nanoseconds per
# engine), amdgpu, and xe (cycles against the GPU's total cycles).
I915 = """pos:\t0
flags:\t02100002
mnt_id:\t26
ino:\t1045
drm-driver:\ti915
drm-client-id:\t7
drm-pdev:\t0000:00:02.0
drm-total-local0:\t0
drm-engine-render:\t{render} ns
drm-engine-copy:\t0 ns
drm-engine-video:\t{video} ns
drm-engine-capacity-video:\t2
drm-engine-video-enhance:\t0 ns
"""
AMD = """pos:\t0
drm-driver:\tamdgpu
drm-client-id:\t12
drm-pdev:\t0000:03:00.0
drm-memory-vram:\t65536 KiB
drm-engine-gfx:\t{gfx} ns
drm-engine-compute:\t0 ns
drm-engine-dec:\t0 ns
"""
XE = """drm-driver:\txe
drm-client-id:\t3
drm-pdev:\t0000:00:02.0
drm-cycles-rcs:\t{cycles}
drm-total-cycles-rcs:\t{total}
"""


def fake_card(root, name, slot, driver, vendor, files=None):
    device = root / "devices" / slot
    device.mkdir(parents=True)
    (device / "vendor").write_text(vendor + "\n")
    drivers = root / "drivers" / driver
    drivers.mkdir(parents=True, exist_ok=True)
    os.symlink(drivers, device / "driver")
    (root / "drm").mkdir(exist_ok=True)
    (root / "drm" / name).mkdir()
    os.symlink(device, root / "drm" / name / "device")
    for file, text in (files or {}).items():
        (device / file).parent.mkdir(parents=True, exist_ok=True)
        (device / file).write_text(text)
    return device


class FakeClients:
    def __init__(self):
        self.readings = []

    def read(self, now):
        return self.readings.pop(0)


class ParseTests(unittest.TestCase):
    def test_i915_engines_and_capacity(self):
        info = gpu.parse_fdinfo(I915.format(render=5_000_000, video=10))
        self.assertEqual((info["driver"], info["pdev"], info["client"]), ("i915", "0000:00:02.0", "7"))
        self.assertEqual(info["engines"]["render"], (5_000_000, 1, "ns"))
        self.assertEqual(info["engines"]["video"], (10, 2, "ns"))
        self.assertNotIn("capacity-video", info["engines"])
        self.assertEqual(info["engines"]["video-enhance"], (0, 1, "ns"))

    def test_other_files_are_skipped(self):
        self.assertIsNone(gpu.parse_fdinfo("pos:\t0\nflags:\t02\nmnt_id:\t15\n"))

    def test_utilization_ns_and_cycles(self):
        old = gpu.parse_fdinfo(I915.format(render=0, video=0))
        new = gpu.parse_fdinfo(I915.format(render=250_000_000, video=1_000_000_000))
        shares = gpu.utilization(old, new, 1_000_000_000)
        self.assertAlmostEqual(shares["render"], 25.0)
        self.assertAlmostEqual(shares["video"], 50.0)        # two video engines
        old = gpu.parse_fdinfo(XE.format(cycles=100, total=1000))
        new = gpu.parse_fdinfo(XE.format(cycles=400, total=2000))
        self.assertAlmostEqual(gpu.utilization(old, new, 1e9)["rcs"], 30.0)

    def test_lspci_name(self):
        def runner(text):
            return lambda *a, **k: type("R", (), {"stdout": text})()
        self.assertEqual(gpu.lspci_name("01:00.0", runner("Slot:\t01:00.0\nVendor:\tNVIDIA Corporation\n"
                                                         "Device:\tAD107 [GeForce RTX 4060]\n")),
                         "NVIDIA GeForce RTX 4060")
        self.assertEqual(gpu.lspci_name("00:01.0", runner("Vendor:\tRed Hat, Inc.\nDevice:\tVirtio 1.0 GPU\n")),
                         "Virtio 1.0 GPU")

    def test_nice_name(self):
        self.assertEqual(gpu.nice_name("AD107 [GeForce RTX 4060]"), "GeForce RTX 4060")
        self.assertEqual(gpu.nice_name("Virtio 1.0 GPU"), "Virtio 1.0 GPU")


class CardTests(unittest.TestCase):
    def test_find_cards_skips_connectors(self):
        root = Path(tempfile.mkdtemp())
        fake_card(root, "card0", "0000:00:02.0", "i915", "0x8086")
        (root / "drm" / "card0-eDP-1").mkdir()
        cards = gpu.find_cards(root / "drm", name_of=lambda slot: "Intel Iris Xe Graphics")
        self.assertEqual([(c["card"], c["slot"], c["driver"], c["vendor"], c["name"]) for c in cards],
                         [("card0", "0000:00:02.0", "i915", "Intel", "Intel Iris Xe Graphics")])

    def test_clients_read_only_drm_fds_of_the_user(self):
        proc = Path(tempfile.mkdtemp())
        for pid, target, text in ((100, "/dev/dri/renderD128", I915.format(render=1, video=0)),
                                  (200, "/home/velt/file.txt", "pos:\t0\n")):
            (proc / str(pid) / "fd").mkdir(parents=True)
            (proc / str(pid) / "fdinfo").mkdir()
            os.symlink(target, proc / str(pid) / "fd" / "5")
            (proc / str(pid) / "fdinfo" / "5").write_text(text)
        (proc / "self").mkdir()
        clients = gpu.Clients(proc=proc, uid=os.getuid()).read(0.0)
        self.assertEqual(list(clients), [(100, "0000:00:02.0", "7")])


class SampleTests(unittest.TestCase):
    def sampler(self, cards, readings, smi=lambda: {}):
        clients = FakeClients()
        clients.readings = readings
        times = iter([0.0, 1.0, 2.0])
        return gpu.Gpus(cards=cards, clients=clients, clock=lambda: next(times), smi=smi)

    def test_intel_from_fdinfo(self):
        root = Path(tempfile.mkdtemp())
        device = fake_card(root, "card0", "0000:00:02.0", "i915", "0x8086")
        card = {"card": "card0", "slot": "0000:00:02.0", "driver": "i915", "vendor": "Intel",
                "name": "Intel Iris Xe Graphics", "device": device}
        first = {(100, "0000:00:02.0", "7"): gpu.parse_fdinfo(I915.format(render=0, video=0)),
                 (300, "0000:00:02.0", "9"): gpu.parse_fdinfo(I915.format(render=0, video=0))}
        second = {(100, "0000:00:02.0", "7"): gpu.parse_fdinfo(I915.format(render=300_000_000, video=0)),
                  (300, "0000:00:02.0", "9"): gpu.parse_fdinfo(I915.format(render=100_000_000, video=0))}
        sampler = self.sampler([card], [first, second])
        (figures,) = sampler.sample()
        self.assertEqual((figures["busy"], figures["source"]), (0.0, "fdinfo"))   # nothing to compare yet
        (figures,) = sampler.sample()
        self.assertAlmostEqual(figures["busy"], 40.0)                              # render: 30 % + 10 %
        self.assertAlmostEqual(sampler.per_process[100], 30.0)
        self.assertAlmostEqual(sampler.per_process[300], 10.0)
        self.assertIsNone(figures["dedicatedTotal"])

    def test_amdgpu_counters(self):
        root = Path(tempfile.mkdtemp())
        device = fake_card(root, "card1", "0000:03:00.0", "amdgpu", "0x1002", {
            "gpu_busy_percent": "57\n", "mem_info_vram_used": str(2 << 30), "mem_info_vram_total": str(8 << 30),
            "mem_info_gtt_used": str(1 << 28), "mem_info_gtt_total": str(4 << 30),
            "hwmon/hwmon3/temp1_input": "61000\n"})
        card = {"card": "card1", "slot": "0000:03:00.0", "driver": "amdgpu", "vendor": "AMD",
                "name": "AMD Radeon RX 6600", "device": device}
        (figures,) = self.sampler([card], [{}]).sample()
        self.assertEqual((figures["busy"], figures["source"]), (57.0, "amdgpu"))
        self.assertEqual((figures["dedicatedUsed"], figures["dedicatedTotal"]), (2 << 30, 8 << 30))
        self.assertEqual(figures["sharedTotal"], 4 << 30)
        self.assertEqual(figures["temperature"], 61.0)

    def test_nvidia_smi_and_no_data(self):
        root = Path(tempfile.mkdtemp())
        nvidia = fake_card(root, "card0", "0000:01:00.0", "nvidia", "0x10de")
        virtio = fake_card(root, "card1", "0000:00:01.0", "virtio-pci", "0x1af4")
        cards = [{"card": "card0", "slot": "0000:01:00.0", "driver": "nvidia", "vendor": "NVIDIA",
                  "name": "NVIDIA GeForce RTX 4060", "device": nvidia},
                 {"card": "card1", "slot": "0000:00:01.0", "driver": "virtio-pci", "vendor": "",
                  "name": "Virtio 1.0 GPU", "device": virtio}]
        out = "00000000:01:00.0, 23, 1500, 8188, 48\n"
        with mock.patch.object(gpu.shutil, "which", return_value="/usr/bin/nvidia-smi"):
            smi = gpu.nvidia_smi(runner=lambda *a, **k: mock.Mock(stdout=out))
        self.assertEqual(smi["0000:01:00.0"], {"busy": 23.0, "used": 1500 << 20, "total": 8188 << 20, "temp": 48.0})
        figures = self.sampler(cards, [{}], smi=lambda: smi).sample()
        self.assertEqual((figures[0]["busy"], figures[0]["temperature"]), (23.0, 48.0))
        self.assertEqual(figures[0]["dedicatedTotal"], 8188 << 20)
        self.assertIsNone(figures[1]["busy"])                    # virtio: no figures at all

    def test_tracking_needs_drm_clients(self):
        sampler = self.sampler([], [])
        sampler.sample()
        self.assertFalse(sampler.tracking)


if __name__ == "__main__":
    unittest.main()
