"""MPRIS: what the desktop's media controls are told about the playing
item (Quick Settings' media card shows the title, artist and cover)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_media import mpris, playqueue  # noqa: E402


class MetadataTests(unittest.TestCase):
    def test_status(self):
        self.assertEqual(mpris.status(mpris.PLAYING), "Playing")
        self.assertEqual(mpris.status(mpris.PAUSED), "Paused")
        self.assertEqual(mpris.status(mpris.STOPPED), "Stopped")

    def test_song(self):
        cover = Path(tempfile.mkdtemp()) / "cover.jpg"
        cover.write_bytes(b"\xff\xd8\xff")
        entry = {"path": "/home/velt/Music/Bloom.flac", "title": "Bloom", "artist": "VeltOS", "album": "Samples",
                 "track": 1, "duration": 63, "cover": str(cover)}
        data = mpris.metadata(entry)
        self.assertEqual(data["xesam:title"], ("s", "Bloom"))
        self.assertEqual(data["xesam:artist"], ("as", ["VeltOS"]))
        self.assertEqual(data["mpris:length"], ("x", 63_000_000))          # microseconds
        self.assertEqual(data["mpris:artUrl"], ("s", cover.as_uri()))
        self.assertEqual(data["xesam:url"], ("s", "file:///home/velt/Music/Bloom.flac"))
        self.assertTrue(data["mpris:trackid"][1].startswith("/org/veltos/media/track/"))
        # The player's own length wins over the library's rounded seconds.
        self.assertEqual(mpris.metadata(entry, 62_500)["mpris:length"], ("x", 62_500_000))

    def test_video_and_nothing(self):
        data = mpris.metadata({"path": "/v/Clip.mp4", "kind": "video", "title": "", "duration": 0})
        self.assertEqual(data["xesam:title"], ("s", "Clip"))
        self.assertNotIn("mpris:length", data)
        self.assertNotIn("mpris:artUrl", data)
        self.assertEqual(mpris.metadata(None), {"mpris:trackid": ("o", "/org/mpris/MediaPlayer2/TrackList/NoTrack")})
        # A cover file that is gone is not announced.
        self.assertNotIn("mpris:artUrl", mpris.metadata({"path": "/a.mp3", "cover": "/nowhere/c.jpg"}))
        # A video's thumbnail stands in for the cover.
        thumb = Path(tempfile.mkdtemp()) / "thumb.png"
        thumb.write_bytes(b"\x89PNG")
        data = mpris.metadata({"path": "/v/Clip.mp4", "kind": "video", "title": "Clip"}, picture=str(thumb))
        self.assertEqual(data["mpris:artUrl"], ("s", thumb.as_uri()))

    def test_track_ids_are_object_paths(self):
        path = mpris.track_id("/home/velt/Müzik/Şarkı (1).mp3")
        self.assertRegex(path, r"^/[A-Za-z0-9_/]+$")
        self.assertEqual(path, mpris.track_id("/home/velt/Müzik/Şarkı (1).mp3"))

    def test_variants(self):
        try:
            from gi.repository import GLib  # noqa: F401
        except ImportError:
            self.skipTest("needs PyGObject (Build-Depends)")
        value = mpris.variant(("a{sv}", mpris.metadata({"path": "/a.mp3", "title": "A", "artist": "B",
                                                         "duration": 2})))
        self.assertEqual(value.get_type_string(), "a{sv}")
        unpacked = value.unpack()
        self.assertEqual(unpacked["xesam:artist"], ["B"])
        self.assertEqual(unpacked["mpris:length"], 2_000_000)

    def test_introspection_is_valid(self):
        try:
            from gi.repository import Gio
        except ImportError:
            self.skipTest("needs PyGObject (Build-Depends)")
        node = Gio.DBusNodeInfo.new_for_xml(mpris.INTROSPECTION)
        names = [iface.name for iface in node.interfaces]
        self.assertEqual(names, [mpris.ROOT_IFACE, mpris.PLAYER_IFACE])


class HasNextTests(unittest.TestCase):
    def test_has_next(self):
        queue = playqueue.PlayQueue()
        self.assertFalse(queue.has_next())
        queue.play([{"path": "a"}, {"path": "b"}], 0)
        self.assertTrue(queue.has_next())
        queue.next()
        self.assertFalse(queue.has_next())
        queue.repeat = "all"
        self.assertTrue(queue.has_next())


if __name__ == "__main__":
    unittest.main()
