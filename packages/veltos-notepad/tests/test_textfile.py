"""Encodings, line endings and positions as Windows 11 Notepad handles them."""

import codecs
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_notepad import textfile  # noqa: E402


class EncodingTests(unittest.TestCase):
    def test_detects_byte_order_marks_and_utf8(self):
        self.assertEqual(textfile.detect_encoding(codecs.BOM_UTF8 + b"x"), ("UTF-8 with BOM", 3))
        self.assertEqual(textfile.detect_encoding(codecs.BOM_UTF16_LE + b"x\0"), ("UTF-16 LE", 2))
        self.assertEqual(textfile.detect_encoding(codecs.BOM_UTF16_BE + b"\0x"), ("UTF-16 BE", 2))
        self.assertEqual(textfile.detect_encoding("Çağrı".encode("utf-8")), ("UTF-8", 0))
        self.assertEqual(textfile.detect_encoding("Çağrı".encode("cp1254")), ("ANSI", 0))

    def test_round_trip_keeps_encoding_and_line_endings(self):
        for encoding in textfile.ENCODINGS:
            for eol in ("CRLF", "LF", "CR"):
                original = "Satır bir\nİkinci satır: şğüöç\n\nson"
                data = textfile.encode(original, encoding, eol, "tr")
                text, found_encoding, found_eol = textfile.decode(data, "tr")
                self.assertEqual(text, original, (encoding, eol))
                self.assertEqual(found_eol, eol, (encoding, eol))
                if encoding != "ANSI":
                    self.assertEqual(found_encoding, encoding)

    def test_ansi_is_the_windows_code_page(self):
        self.assertEqual(textfile.encode("ğ", "ANSI", "LF", "tr"), "ğ".encode("cp1254"))
        self.assertEqual(textfile.encode("€", "ANSI", "LF", "en"), b"\x80")
        self.assertEqual(textfile.encode("ğ", "ANSI", "LF", "en"), b"?")   # not in cp1252

    def test_line_ending_detection(self):
        self.assertEqual(textfile.detect_eol("a\r\nb\r\nc\n"), "CRLF")
        self.assertEqual(textfile.detect_eol("a\nb\n"), "LF")
        self.assertEqual(textfile.detect_eol("a\rb\r"), "CR")
        self.assertEqual(textfile.detect_eol("one line"), "LF")
        self.assertEqual(textfile.detect_eol("one line", "CRLF"), "CRLF")
        text, _enc, eol = textfile.decode(b"a\r\nb\rc\n", "en")
        self.assertEqual(text, "a\nb\nc\n")
        self.assertEqual(eol, "CRLF")


class FileTests(unittest.TestCase):
    def test_save_is_atomic_and_keeps_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "notes.txt")
            path.write_bytes(b"old")
            os.chmod(path, 0o640)
            textfile.save(path, "new\ntext", "UTF-8", "CRLF")
            self.assertEqual(path.read_bytes(), b"new\r\ntext")
            if os.name == "posix":
                self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["notes.txt"])
            self.assertEqual(textfile.load(path), ("new\ntext", "UTF-8", "CRLF"))

    def test_refuses_folders_and_huge_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(OSError):
                textfile.load(tmp)
            big = Path(tmp, "big.log")
            with big.open("wb") as out:
                out.truncate(textfile.MAX_BYTES + 1)
            with self.assertRaises(OSError):
                textfile.load(big)


class PositionTests(unittest.TestCase):
    def test_line_and_column(self):
        text = "ab\ncde\n\nf"
        self.assertEqual(textfile.line_column(text, 0), (1, 1))
        self.assertEqual(textfile.line_column(text, 2), (1, 3))
        self.assertEqual(textfile.line_column(text, 3), (2, 1))
        self.assertEqual(textfile.line_column(text, 7), (3, 1))
        self.assertEqual(textfile.line_column(text, 8), (4, 1))
        self.assertEqual(textfile.line_column(text, 99), (4, 2))
        self.assertEqual(textfile.line_start(text, 2), 3)
        self.assertEqual(textfile.line_start(text, 4), 8)
        self.assertEqual(textfile.line_start(text, 40), 8)


if __name__ == "__main__":
    unittest.main()
