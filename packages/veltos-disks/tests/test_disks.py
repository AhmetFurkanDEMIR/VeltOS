"""disks.py: UDisks2 objects become Windows' disks and volumes; the UDisks2
calls are built right. app.Backend: texts, what is allowed, the calls
made (recorded, nothing runs)."""

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_disks import disks  # noqa: E402

MIB, GIB = disks.MIB, disks.GIB
DRIVES = "/org/freedesktop/UDisks2/drives/"
BLOCKS = "/org/freedesktop/UDisks2/block_devices/"


def sample_objects():
    """Disk 0: GPT with an EFI partition (/boot/efi), the root (/) and
    9.5 GB unallocated; Disk 1: a USB stick (MBR, one NTFS partition, not
    mounted); CD-ROM 0 without a disc; a loop device without a drive."""
    def drive(vendor, model, size, removable=False, optical=False):
        return {"Drive": {"Vendor": vendor, "Model": model, "Size": size, "Removable": removable,
                          "MediaRemovable": optical, "Optical": optical}}

    def block(device, drive_path, size, **more):
        data = {"Device": device, "Drive": drive_path, "Size": size, "ReadOnly": False, "HintIgnore": False,
                "IdUsage": "", "IdType": "", "IdVersion": "", "IdLabel": "", "IdUUID": ""}
        data.update(more)
        return data

    return {
        DRIVES + "VBOX_HARDDISK": drive("VBOX", "HARDDISK", 40 * GIB),
        DRIVES + "Kingston": drive("Kingston", "DataTraveler", 8 * GIB, removable=True),
        DRIVES + "QEMU_DVD": drive("QEMU", "DVD-ROM", 0, removable=True, optical=True),
        BLOCKS + "sda": {"Block": block("/dev/sda", DRIVES + "VBOX_HARDDISK", 40 * GIB),
                         "PartitionTable": {"Type": "gpt"}},
        BLOCKS + "sda1": {"Block": block("/dev/sda1", DRIVES + "VBOX_HARDDISK", 512 * MIB, IdUsage="filesystem",
                                         IdType="vfat", IdVersion="FAT32", IdUUID="1234-ABCD"),
                          "Partition": {"Table": BLOCKS + "sda", "Number": 1, "Offset": MIB, "Size": 512 * MIB,
                                        "Type": "c12a7328-f81f-11d2-ba4b-00a0c93ec93b", "Name": "EFI"},
                          "Filesystem": {"MountPoints": ["/boot/efi"]}},
        BLOCKS + "sda2": {"Block": block("/dev/sda2", DRIVES + "VBOX_HARDDISK", 30 * GIB, IdUsage="filesystem",
                                         IdType="ext4", IdUUID="abcd"),
                          "Partition": {"Table": BLOCKS + "sda", "Number": 2, "Offset": 513 * MIB, "Size": 30 * GIB,
                                        "Type": "0fc63daf-8483-4772-8e79-3d69d8477de4", "Name": ""},
                          "Filesystem": {"MountPoints": ["/"]}},
        BLOCKS + "sdb": {"Block": block("/dev/sdb", DRIVES + "Kingston", 8 * GIB), "PartitionTable": {"Type": "dos"}},
        BLOCKS + "sdb1": {"Block": block("/dev/sdb1", DRIVES + "Kingston", 8 * GIB - 2 * MIB, IdUsage="filesystem",
                                         IdType="ntfs", IdLabel="USB"),
                          "Partition": {"Table": BLOCKS + "sdb", "Number": 1, "Offset": MIB, "Size": 8 * GIB - 2 * MIB,
                                        "Type": "0x07", "Name": ""},
                          "Filesystem": {"MountPoints": []}},
        BLOCKS + "sr0": {"Block": block("/dev/sr0", DRIVES + "QEMU_DVD", 0)},
        BLOCKS + "loop0": {"Block": block("/dev/loop0", "/", 100 * MIB)},
        # A blank disk (no partition table): "Not Initialized", Initialize Disk offered.
        DRIVES + "VirtIO_Disk": drive("", "", 40 * GIB),
        BLOCKS + "vda": {"Block": block("/dev/vda", DRIVES + "VirtIO_Disk", 40 * GIB)},
    }


def fake_statvfs(path):
    free = {"/": 20 * GIB, "/boot/efi": 400 * MIB}
    if path not in free:
        raise OSError(path)
    return SimpleNamespace(f_bavail=free[path] // 4096, f_frsize=4096)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.disks = disks.build(sample_objects(), fake_statvfs)

    def test_disks_in_windows_order(self):
        self.assertEqual([(d["kind"], d["number"], d["device"]) for d in self.disks],
                         [("disk", 0, "/dev/sda"), ("disk", 1, "/dev/sdb"), ("disk", 2, "/dev/vda"),
                          ("cdrom", 0, "/dev/sr0")])
        self.assertEqual(self.disks[0]["model"], "VBOX HARDDISK")
        self.assertTrue(self.disks[1]["removable"])
        self.assertFalse(self.disks[3]["media"])
        self.assertEqual(self.disks[3]["segments"], [])
        blank = self.disks[2]
        self.assertIsNone(blank["table"])
        self.assertEqual([(s["kind"], s["size"]) for s in blank["segments"]], [("unallocated", 40 * GIB)])

    def test_partitions_and_unallocated_space(self):
        segments = self.disks[0]["segments"]
        self.assertEqual([s["kind"] for s in segments], ["volume", "volume", "unallocated"])
        efi, root, gap = segments
        self.assertEqual((efi["role"], efi["fs"], efi["mounts"], efi["system"]), ("efi", "FAT32", ["/boot/efi"], True))
        self.assertEqual((root["role"], root["fs"], root["system"], root["free"]), ("data", "ext4", True, 20 * GIB))
        self.assertEqual(gap["size"], 40 * GIB - 513 * MIB - 30 * GIB)
        self.assertEqual([s["index"] for s in segments], [0, 1, 2])
        usb = self.disks[1]["segments"]
        self.assertEqual([(s["kind"], s["role"], s["label"], s["mounts"], s["free"]) for s in usb],
                         [("volume", "primary", "USB", [], None)])
        self.assertEqual(len(disks.volumes(self.disks)), 3)

    def test_texts(self):
        self.assertEqual(disks.size_text(512 * MIB), "512 MB")
        self.assertEqual(disks.size_text(40 * GIB), "40.00 GB")
        self.assertEqual(disks.size_text(40 * GIB, "tr"), "40,00 GB")
        self.assertEqual(disks.size_text(int(1.5 * disks.TIB)), "1.50 TB")
        self.assertEqual(disks.fs_name({"IdType": "vfat", "IdVersion": "FAT32"}), "FAT32")
        self.assertEqual(disks.fs_name({"IdType": "ntfs"}), "NTFS")
        self.assertEqual(disks.fs_name({}), "RAW")
        self.assertEqual(disks.role_of({"Type": "0x82"}, "dos"), "swap")
        self.assertEqual(disks.role_of({"Type": "0x83", "IsContained": True}, "dos"), "logical")

    def test_udisks_calls(self):
        head = ["busctl", "--system", "--json=short", "call", disks.SERVICE]
        self.assertEqual(disks.format_command(BLOCKS + "sdb1", "ntfs", "Data", True),
                         head + [BLOCKS + "sdb1", "org.freedesktop.UDisks2.Block", "Format", "sa{sv}", "ntfs",
                                 "1", "label", "s", "Data"])
        create = disks.create_command(BLOCKS + "sda", "gpt", 31 * GIB, 0, "ext4", "", True)
        self.assertEqual(create[5:9], [BLOCKS + "sda", "org.freedesktop.UDisks2.PartitionTable",
                                       "CreatePartitionAndFormat", "ttssa{sv}sa{sv}"])
        self.assertEqual(create[9:14], [str(31 * GIB), "0", "0fc63daf-8483-4772-8e79-3d69d8477de4", "", "0"])
        self.assertEqual(create[14:], ["ext4", "1", "take-ownership", "b", "true"])
        self.assertEqual(disks.create_command(BLOCKS + "sdb", "dos", MIB, 0, "ntfs", "X", False)[11:14],
                         ["0x07", "", "0"])
        self.assertEqual(disks.delete_command(BLOCKS + "sdb1")[6:9],
                         ["org.freedesktop.UDisks2.Partition", "Delete", "a{sv}"])
        self.assertEqual(disks.initialize_command(BLOCKS + "sdb", "gpt")[7:10], ["Format", "sa{sv}", "gpt"])
        self.assertEqual(disks.eject_command(DRIVES + "Kingston")[6:8], ["org.freedesktop.UDisks2.Drive", "Eject"])
        self.assertEqual(disks.error_text("x\nCall failed: Device is mounted"), "Device is mounted")
        self.assertEqual(disks.mount_point_of('{"type":"s","data":["/media/velt/USB"]}'), "/media/velt/USB")
        self.assertEqual(disks.mount_point_of("nonsense"), "")

    def test_available_formats_follow_the_mkfs_programs(self):
        found = {"mkfs.ntfs": "/usr/sbin/mkfs.ntfs", "mkfs.ext4": "/usr/sbin/mkfs.ext4", "mkfs.fat": "/usr/sbin/mkfs.fat"}
        self.assertEqual(disks.available_formats(which=found.get), ["ntfs", "vfat", "ext4"])
        self.assertEqual(disks.available_formats(which=lambda program: None), [])
        self.assertIn("/usr/sbin", disks.MKFS_PATH)

    def test_objects_from_busctl_json(self):
        text = ('{"type":"a{oa{sa{sv}}}","data":[{"/org/freedesktop/UDisks2/block_devices/sda":'
                '{"org.freedesktop.UDisks2.Block":{"Device":{"type":"ay","data":[47,100,101,118,47,115,100,97,0]},'
                '"Size":{"type":"t","data":1000}}}}]}')
        objects = disks.objects_from_json(text)
        self.assertEqual(objects[BLOCKS + "sda"]["Block"], {"Device": "/dev/sda", "Size": 1000})


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtGui import QGuiApplication
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class BackendTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        os.environ["XDG_CONFIG_HOME"] = str(Path(__file__).resolve().parent / "no-config")
        # A GUI application (not QCoreApplication): the window tests in
        # the same process reuse it, and QML windows need one (abort).
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        from veltos_disks import app
        self.calls, self.started, self.messages = [], [], []
        self.replies = {}

        def runner(command):
            self.calls.append(command)
            return self.replies.get(command[7], (0, "", ""))

        self.backend = app.Backend(lang=self.lang, reader=sample_objects, runner=runner,
                                   start=self.started.append, formats=["ntfs", "ext4"], threaded=False,
                                   statvfs=fake_statvfs)
        self.backend.message.connect(self.messages.append)

    def volume(self, name):
        return next(v for v in self.backend.volumes if v["device"] == "/dev/" + name)

    def test_views(self):
        titles = [d["title"] for d in self.backend.disks]
        self.assertEqual(titles, ["Disk 0", "Disk 1", "Disk 2", "CD-ROM 0"])
        self.assertEqual([d["statusText"] for d in self.backend.disks],
                         ["Online", "Online", "Not Initialized", "No Media"])
        self.assertEqual(self.backend.disks[1]["kindText"], "Removable")
        root = self.volume("sda2")
        self.assertEqual((root["title"], root["statusText"], root["fsText"], root["percentFree"]),
                         ("Local Disk", "Healthy (Basic Data Partition, System)", "ext4", "67 %"))
        self.assertEqual(self.volume("sda1")["statusText"], "Healthy (EFI System Partition)")
        usb = self.volume("sdb1")
        self.assertEqual((usb["title"], usb["statusText"], usb["mounted"], usb["canFormat"], usb["canDelete"]),
                         ("USB", "Healthy (Primary Partition)", False, True, True))
        self.assertEqual((usb["canMount"], usb["canUnmount"], usb["canEject"]), (True, False, True))
        self.assertFalse(root["canFormat"])
        self.assertEqual(self.backend.disks[0]["segments"][2]["title"], "Unallocated")

    def test_system_volumes_are_safe(self):
        root = self.volume("sda2")
        self.assertFalse(self.backend.act("format", root["object"], {"fs": "ntfs"}))
        self.assertFalse(self.backend.act("delete", root["object"], {}))
        self.assertEqual(self.calls, [])
        self.assertEqual(self.messages, [self.backend.texts["system_volume"]] * 2)
        self.assertFalse(self.backend.act("delete", self.volume("sda1")["object"], {}))   # EFI
        # A disk with a partition table is never initialized again; a blank one is.
        self.assertFalse(self.backend.act("initialize", BLOCKS + "sdb", {"style": "gpt"}))
        self.assertTrue(self.backend.act("initialize", BLOCKS + "vda", {"style": "gpt"}))
        self.assertEqual(self.calls[-1], disks.initialize_command(BLOCKS + "vda", "gpt"))

    def test_format_delete_create(self):
        usb = self.volume("sdb1")
        self.assertTrue(self.backend.act("format", usb["object"], {"fs": "ntfs", "label": "Data", "quick": True}))
        self.assertEqual(self.calls, [disks.format_command(usb["object"], "ntfs", "Data", True)])
        self.assertFalse(self.backend.busy)
        self.assertTrue(self.backend.act("delete", usb["object"], {}))
        self.assertEqual(self.calls[-1], disks.delete_command(usb["object"]))
        gap = self.backend.disks[0]["segments"][2]
        self.assertTrue(self.backend.act("create", BLOCKS + "sda", {"offset": gap["offset"], "size": 0, "fs": "ext4",
                                                                     "label": "New", "quick": True}))
        self.assertEqual(self.calls[-1], disks.create_command(BLOCKS + "sda", "gpt", gap["offset"], 0, "ext4", "New", True))
        self.assertFalse(self.backend.act("create", BLOCKS + "sda", {"offset": 0, "size": 0, "fs": "btrfs"}))
        self.assertEqual(self.messages, [])

    def test_open_mounts_first_and_errors_are_reported(self):
        usb = self.volume("sdb1")
        self.replies["Mount"] = (0, '{"type":"s","data":["/media/velt/USB"]}', "")
        self.assertTrue(self.backend.act("open", usb["object"], {}))
        self.assertEqual(self.calls, [disks.mount_command(usb["object"])])
        self.assertEqual(self.started, [["veltos-explorer", "/media/velt/USB"]])
        self.assertTrue(self.backend.act("open", self.volume("sda2")["object"], {}))     # mounted: no call
        self.assertEqual(self.started[-1], ["veltos-explorer", "/"])
        self.replies["Eject"] = (1, "", "Call failed: Device is busy")
        self.assertTrue(self.backend.act("eject", usb["object"], {}))
        self.assertEqual(self.messages, [self.backend.texts["failed"].format(error="Device is busy")])
        self.assertFalse(self.backend.busy)


class TurkishBackendTests(BackendTests):
    lang = "tr"

    def test_views(self):
        self.assertEqual(self.backend.texts["app_title"], "Disk Yönetimi")
        self.assertEqual(self.volume("sda2")["title"], "Yerel Disk")
        self.assertEqual(self.volume("sda2")["statusText"], "İyi durumda (Temel Veri Bölümü, Sistem)")
        self.assertEqual(self.backend.disks[0]["sizeText"], "40,00 GB")
        self.assertEqual(self.backend.disks[2]["statusText"], "Başlatılmamış")
        self.assertEqual(self.backend.disks[3]["statusText"], "Ortam Yok")

    def test_system_volumes_are_safe(self):
        self.assertFalse(self.backend.act("format", self.volume("sda2")["object"], {"fs": "ntfs"}))
        self.assertEqual(self.messages, ["Bu birim çalışan sistem tarafından kullanılıyor ve değiştirilemez."])


if __name__ == "__main__":
    unittest.main()
