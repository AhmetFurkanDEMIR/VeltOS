"""The play queue (shuffle, repeat) and the library (tags of real WAV files
written with mutagen) of VeltOS Media Player."""

import random
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_media import library, playqueue  # noqa: E402

try:
    import mutagen  # noqa: F401
    HAVE_MUTAGEN = True
except ImportError:
    HAVE_MUTAGEN = False


def make_wav(path, seconds=1, title=None, artist=None, album=None, track=None):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(8000)
        out.writeframes(struct.pack("<h", 0) * 8000 * seconds)
    if title is not None:
        from mutagen.id3 import TALB, TIT2, TPE1, TRCK
        from mutagen.wave import WAVE
        audio = WAVE(str(path))
        audio.add_tags()
        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=artist or ""))
        audio.tags.add(TALB(encoding=3, text=album or ""))
        if track:
            audio.tags.add(TRCK(encoding=3, text=str(track)))
        audio.save()


def items(*names):
    return [{"path": f"/m/{n}"} for n in names]


class QueueTests(unittest.TestCase):
    def test_in_order_and_repeat(self):
        q = playqueue.PlayQueue()
        self.assertEqual(q.play(items("a", "b", "c"), 1)["path"], "/m/b")
        self.assertEqual(q.next(finished=True)["path"], "/m/c")
        self.assertIsNone(q.next(finished=True))           # repeat off: the end
        q.repeat = "all"
        self.assertEqual(q.next(finished=True)["path"], "/m/a")
        q.repeat = "one"
        self.assertEqual(q.next(finished=True)["path"], "/m/a")
        self.assertEqual(q.next(finished=False)["path"], "/m/b")   # "Next" skips even with repeat one
        self.assertEqual(q.cycle_repeat(), "off")

    def test_previous_and_remove(self):
        q = playqueue.PlayQueue()
        q.play(items("a", "b", "c"), 2)
        self.assertEqual(q.previous()["path"], "/m/b")
        q.remove(0)                                        # a, before the current one
        self.assertEqual(q.current["path"], "/m/b")
        self.assertEqual([i["path"] for i in q.in_order()], ["/m/b", "/m/c"])
        q.add(items("d"))
        self.assertEqual([i["path"] for i in q.in_order()], ["/m/b", "/m/c", "/m/d"])
        q.clear()
        self.assertIsNone(q.current)

    def test_shuffle_keeps_the_playing_item_first(self):
        q = playqueue.PlayQueue(rng=random.Random(4))
        q.play(items(*"abcdefgh"), 3)
        q.set_shuffle(True)
        order = [i["path"] for i in q.in_order()]
        self.assertEqual(order[0], "/m/d")
        self.assertEqual(q.current["path"], "/m/d")
        self.assertEqual(sorted(order), [f"/m/{c}" for c in "abcdefgh"])
        q.set_shuffle(False)
        self.assertEqual(q.current["path"], "/m/d")
        self.assertEqual([i["path"] for i in q.in_order()], [f"/m/{c}" for c in "abcdefgh"])


@unittest.skipUnless(HAVE_MUTAGEN, "needs mutagen (Build-Depends)")
class LibraryTests(unittest.TestCase):
    def test_scan_songs_albums_artists_and_videos(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "Music/Band - First").mkdir(parents=True)
        (tmp / "Videos").mkdir()
        make_wav(tmp / "Music/Band - First/02.wav", 2, "Second Song", "The Band", "First", 2)
        make_wav(tmp / "Music/Band - First/01.wav", 1, "First Song", "The Band", "First", 1)
        make_wav(tmp / "Music/loose.wav")
        (tmp / "Music/Band - First/cover.jpg").write_bytes(b"\xff\xd8 not really a jpeg")
        (tmp / "Videos/clip.mp4").write_bytes(b"\0" * 64)
        songs, videos = library.scan([tmp / "Music"], [tmp / "Videos"], tmp / "covers")
        titles = [s["title"] for s in songs]
        self.assertEqual(titles, ["loose", "First Song", "Second Song"])     # by album artist, album, track
        first = songs[1]
        self.assertEqual((first["artist"], first["album"], first["track"]), ("The Band", "First", 1))
        self.assertEqual(songs[2]["duration"], 2)
        self.assertTrue(first["cover"].endswith("cover.jpg"))                # folder picture
        self.assertEqual([v["title"] for v in videos], ["clip"])
        albums = library.albums(songs)
        self.assertEqual([(a["title"], len(a["songs"])) for a in albums], [("", 1), ("First", 2)])
        self.assertEqual([a["name"] for a in library.artists(songs)], ["", "The Band"])
        cache = {e["path"]: e for e in songs + videos}
        self.assertEqual(library.scan([tmp / "Music"], [tmp / "Videos"], tmp / "covers", cache), (songs, videos))

    def test_duration_text(self):
        self.assertEqual(library.duration_text(65), "1:05")
        self.assertEqual(library.duration_text(3725), "1:02:05")
        self.assertEqual(library.duration_text(0), "0:00")


if __name__ == "__main__":
    unittest.main()
