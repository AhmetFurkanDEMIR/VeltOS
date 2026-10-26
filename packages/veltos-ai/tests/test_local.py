"""VeltOS AI's local model without network or llama-server: downloads
(progress, size and SHA-256 checks, cancel), Hugging Face's listings, the
model folder, the engine's start, and the local adapter's stream."""

import hashlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from veltos_ai import local, providers  # noqa: E402
import fakeservice as fake  # noqa: E402


class Response(io.BytesIO):
    status = 200

    def __init__(self, data, length=True):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))} if length else {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class Opener:
    """Serves bytes (or a JSON-able object) for every request and records the URLs."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.urls = []

    def __call__(self, request, timeout=None):
        self.urls.append(request if isinstance(request, str) else request.full_url)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        if not isinstance(answer, bytes):
            answer = json.dumps(answer).encode()
        return Response(answer)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.data = os.urandom(300_000)
        self.sha = hashlib.sha256(self.data).hexdigest()

    def test_download_checks_size_and_sha(self):
        seen = []
        target = self.folder / "m.gguf"
        self.assertTrue(local.download("https://x/m.gguf", target, len(self.data), self.sha,
                                       lambda *p: seen.append(p), None, Opener(self.data)))
        self.assertEqual(target.read_bytes(), self.data)
        self.assertEqual(seen[-1][0], len(self.data))
        self.assertFalse((self.folder / "m.gguf.part").exists())

    def test_wrong_sha_or_size_keeps_nothing(self):
        target = self.folder / "m.gguf"
        with self.assertRaises(local.DownloadError):
            local.download("https://x/m.gguf", target, len(self.data), "0" * 64, None, None, Opener(self.data))
        with self.assertRaises(local.DownloadError):
            local.download("https://x/m.gguf", target, len(self.data) + 1, "", None, None, Opener(self.data))
        with self.assertRaises(local.DownloadError):
            local.download("https://x/m.gguf", target, 0, "", None, None, Opener(OSError("offline")))
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_cancel(self):
        cancel = threading.Event()
        cancel.set()
        target = self.folder / "m.gguf"
        self.assertFalse(local.download("https://x/m.gguf", target, 0, "", None, cancel, Opener(self.data)))
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_model_folder(self):
        (self.folder / "a.gguf").write_bytes(b"12")
        (self.folder / "b.gguf.part").write_bytes(b"1")
        (self.folder / "notes.txt").write_bytes(b"1")
        self.assertEqual(local.installed(self.folder), [{"file": "a.gguf", "size": 2}])
        self.assertEqual(local.model_path("a.gguf", self.folder), self.folder / "a.gguf")
        self.assertIsNone(local.model_path("../a.gguf", self.folder.parent / "x"))
        self.assertEqual(local.safe_name("../../etc/x.gguf"), "x.gguf")
        self.assertEqual(local.safe_name("x.bin"), "")
        self.assertEqual(local.safe_name(".hidden.gguf"), "")

    def test_default_model_is_pinned(self):
        d = local.DEFAULT_MODEL
        self.assertRegex(d["revision"], "^[0-9a-f]{40}$")
        self.assertRegex(d["sha256"], "^[0-9a-f]{64}$")
        self.assertTrue(100e6 <= d["size"] <= 200e6)      # the product owner's 100-200 MB
        self.assertEqual(local.resolve_url(d["repo"], d["file"], d["revision"]),
                         "https://huggingface.co/unsloth/gemma-3-270m-it-GGUF/resolve/"
                         "c90975dbd40c0c7b275fefaae758c3415c906238/gemma-3-270m-it-UD-IQ3_XXS.gguf")
        self.assertEqual(local.size_text(d["size"]), "185 MB")
        self.assertEqual(local.size_text(1_234_000_000), "1.2 GB")


class HubTests(unittest.TestCase):
    def test_search_leaves_gated_repositories_out(self):
        opener = Opener([{"id": "a/one-GGUF", "downloads": 10, "likes": 1, "gated": False},
                         {"id": "b/gated-GGUF", "downloads": 9, "gated": "manual"},
                         {"id": "c/private", "private": True}])
        found = local.search("gemma 270m", opener)
        self.assertEqual(found, [{"repo": "a/one-GGUF", "downloads": 10, "likes": 1}])
        self.assertIn("filter=gguf", opener.urls[0])
        self.assertIn("search=gemma+270m", opener.urls[0])

    def test_repo_files_smallest_first_without_projectors(self):
        opener = Opener([
            {"type": "file", "path": "README.md", "size": 5},
            {"type": "file", "path": "m-Q8_0.gguf", "size": 1, "lfs": {"size": 300, "oid": "b" * 64}},
            {"type": "file", "path": "m-Q4.gguf", "size": 1, "lfs": {"size": 200, "oid": "a" * 64}},
            {"type": "file", "path": "mmproj-F16.gguf", "lfs": {"size": 50}},
            {"type": "directory", "path": "sub"},
        ])
        files = local.repo_files("a/one-GGUF", opener)
        self.assertEqual([f["file"] for f in files], ["m-Q4.gguf", "m-Q8_0.gguf"])
        self.assertEqual(files[0]["sha256"], "a" * 64)
        self.assertTrue(opener.urls[0].endswith("/api/models/a/one-GGUF/tree/main"))
        with self.assertRaises(local.DownloadError):
            local.repo_files("../etc", Opener())


class Process:
    def __init__(self, args, **kw):
        self.args = args
        self.ended = None

    def poll(self):
        return self.ended

    def terminate(self):
        self.ended = 0

    def wait(self, timeout=None):
        return 0


class ServerTests(unittest.TestCase):
    def test_starts_on_the_loopback_and_reuses_the_process(self):
        program = Path(tempfile.mkdtemp()) / "llama-server"
        program.write_text("#!/bin/sh\n")
        program.chmod(0o755)
        started = []

        def popen(args, **kw):
            started.append(Process(args))
            return started[-1]
        server = local.Server(str(program), popen, Opener(b"{}", b"{}"))
        base = server.base("/m/a.gguf")
        self.assertTrue(base.startswith("http://127.0.0.1:"))
        self.assertEqual(server.base("/m/a.gguf"), base)
        self.assertEqual(len(started), 1)
        args = started[0].args
        self.assertEqual(args[args.index("--host") + 1], "127.0.0.1")
        self.assertIn("--no-webui", args)
        server.base("/m/b.gguf")                         # another model: a new server
        self.assertEqual(len(started), 2)
        self.assertEqual(started[0].ended, 0)
        server.stop()
        self.assertEqual(started[1].ended, 0)

    def test_without_the_engine(self):
        server = local.Server("/nonexistent/llama-server")
        with self.assertRaises(local.DownloadError):
            server.base("/m/a.gguf")


class FakeServer:
    def base(self, model):
        return "http://127.0.0.1:9"


class LocalAdapterTests(unittest.TestCase):
    def test_stream(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "m.gguf").write_bytes(b"gguf")
        old = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = str(folder.parent / "data")
        models = local.models_dir()
        models.mkdir(parents=True)
        (models / "m.gguf").write_bytes(b"gguf")
        try:
            adapter = providers.Local({"model": "m.gguf"}, FakeServer())
            answer = fake.sse([{"choices": [{"delta": {"content": "Mer"}}]},
                               {"choices": [{"delta": {"content": "haba"}, "finish_reason": "stop"}]}, "[DONE]"])
            service = fake.FakeService(answer)
            history = []
            adapter.add_user(history, "Selam")
            events = list(providers.stream(adapter, history, "system", [], service))
            request = service.requests[0]
            self.assertEqual(request["url"], "http://127.0.0.1:9/v1/chat/completions")
            self.assertEqual(request["body"]["messages"][-1], {"role": "user", "content": "Selam"})
            self.assertNotIn("tools", request["body"])
            self.assertEqual("".join(d for k, d in events if k == "text"), "Merhaba")
            missing = providers.Local({"model": "gone.gguf"}, FakeServer())
            with self.assertRaises(providers.ServiceError):
                list(providers.stream(missing, [{"role": "user", "content": "x"}], "s", [], service))
        finally:
            if old is None:
                os.environ.pop("XDG_DATA_HOME", None)
            else:
                os.environ["XDG_DATA_HOME"] = old


if __name__ == "__main__":
    unittest.main()
