"""VeltOS AI's local model: a small language model on this PC, free and
offline once downloaded (product owner, 2026-10-26).

- The model files (GGUF) live in ~/.local/share/veltos/ai-models.
- The default is Google's Gemma 3 270M (instruction tuned, many languages
  including Turkish and English) in a 185 MB quantisation, pinned to one
  revision of unsloth's repository on Hugging Face and checked against its
  SHA-256 after the download. Other models come from Hugging Face's public
  API (search, then a repository's .gguf files with their sizes and LFS
  SHA-256); gated repositories need a sign-in and are not offered.
- veltos-llama's `llama-server` (llama.cpp, built from a pinned source by
  VeltOS) runs the chosen model on 127.0.0.1 with an OpenAI-compatible API;
  VeltOS AI starts it when the local model is first asked something and
  stops it when it quits. It listens on the loopback only.

Standard library only; downloads report progress through a callback and
stop when the cancel event is set.
"""

import hashlib
import json
import os
import socket
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

SERVER = "/usr/libexec/veltos/llama-server"      # veltos-llama
HUB = "https://huggingface.co"
USER_AGENT = "VeltOS-AI/1.0 (+https://veltos.ahmetfurkandemir.com)"
CHUNK = 1 << 16

DEFAULT_MODEL = {
    "repo": "unsloth/gemma-3-270m-it-GGUF",
    "revision": "c90975dbd40c0c7b275fefaae758c3415c906238",
    "file": "gemma-3-270m-it-UD-IQ3_XXS.gguf",
    "size": 184517664,
    "sha256": "a406b0dbc761a841c522146168b4bd0589bcb739c444f45356105715d438d126",
    "title": "Gemma 3 270M (Google)",
    "license": "https://ai.google.dev/gemma/terms",
}


def models_dir():
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    return base / "veltos" / "ai-models"


def safe_name(name):
    """A model file name to keep: no folders, a .gguf ending."""
    name = Path(str(name)).name
    if not name.endswith(".gguf") or name.startswith("."):
        return ""
    return name


def installed(directory=None):
    """[{"file", "size"}] of the downloaded models, by name."""
    folder = Path(directory or models_dir())
    if not folder.is_dir():
        return []
    return [{"file": p.name, "size": p.stat().st_size}
            for p in sorted(folder.glob("*.gguf")) if p.is_file()]


def model_path(name, directory=None):
    name = safe_name(name)
    if not name:
        return None
    path = Path(directory or models_dir()) / name
    return path if path.is_file() else None


def engine_available():
    return os.access(SERVER, os.X_OK)


def size_text(size):
    """"185 MB", "1.2 GB" (decimal, as Hugging Face shows sizes)."""
    if size >= 1e9:
        return f"{size / 1e9:.1f} GB"
    return f"{max(1, round(size / 1e6))} MB"


# --- downloads ---------------------------------------------------------------------------------

def resolve_url(repo, file, revision="main"):
    return f"{HUB}/{repo}/resolve/{revision}/{urllib.parse.quote(file)}"


class DownloadError(Exception):
    pass


def download(url, target, size=0, sha256="", progress=None, cancel=None, opener=None):
    """Downloads `url` to `target` (through target.part, renamed at the end),
    calling progress(done, total, bytes_per_second). Checks the size and the
    SHA-256 when known. Returns False when cancelled; raises DownloadError."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    done, started, last = 0, time.monotonic(), 0.0
    try:
        with (opener or urllib.request.urlopen)(request, timeout=60) as response, open(partial, "wb") as out:
            total = size or int(response.headers.get("Content-Length") or 0)
            while True:
                if cancel is not None and cancel.is_set():
                    raise InterruptedError
                chunk = response.read(CHUNK)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                done += len(chunk)
                now = time.monotonic()
                if progress and (now - last > 0.2 or done == total):
                    last = now
                    progress(done, total, done / max(0.001, now - started))
    except InterruptedError:
        partial.unlink(missing_ok=True)
        return False
    except OSError as error:   # urllib's errors are OSErrors
        partial.unlink(missing_ok=True)
        raise DownloadError(str(getattr(error, "reason", error))) from error
    if size and done != size:
        partial.unlink(missing_ok=True)
        raise DownloadError(f"the file has {done} bytes, {size} were expected")
    if sha256 and digest.hexdigest() != sha256:
        partial.unlink(missing_ok=True)
        raise DownloadError("the file's SHA-256 does not match")
    os.replace(partial, target)
    return True


# --- Hugging Face -------------------------------------------------------------------------------

def hub_json(path, opener=None):
    request = urllib.request.Request(HUB + path, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as error:
        raise DownloadError(str(getattr(error, "reason", error))) from error


def search(query, opener=None, limit=20):
    """Public GGUF repositories matching the words, most downloaded first:
    [{"repo", "downloads", "likes"}]. Gated repositories are left out."""
    params = urllib.parse.urlencode({"search": query.strip(), "filter": "gguf", "sort": "downloads",
                                     "direction": "-1", "limit": str(limit * 2), "full": "false"})
    found = []
    for model in hub_json("/api/models?" + params, opener) or []:
        if model.get("gated") not in (False, None) or model.get("private"):
            continue
        found.append({"repo": model.get("id") or model.get("modelId", ""),
                      "downloads": int(model.get("downloads") or 0), "likes": int(model.get("likes") or 0)})
        if len(found) >= limit:
            break
    return found


def repo_files(repo, opener=None):
    """The .gguf files of a repository with size and SHA-256, smallest first."""
    if not repo or ".." in repo or repo.count("/") != 1:
        raise DownloadError("not a repository name")
    files = []
    for entry in hub_json(f"/api/models/{repo}/tree/main", opener) or []:
        name = entry.get("path", "")
        if entry.get("type") != "file" or not safe_name(name) or "/" in name or "mmproj" in name.lower():
            continue
        lfs = entry.get("lfs") or {}
        files.append({"file": name, "size": int(lfs.get("size") or entry.get("size") or 0),
                      "sha256": lfs.get("oid", "")})
    return sorted(files, key=lambda f: f["size"])


# --- the engine ---------------------------------------------------------------------------------

def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Server:
    """One llama-server for the chosen model, started on demand."""

    def __init__(self, program=SERVER, popen=subprocess.Popen, opener=None):
        self.program = program
        self.popen = popen
        self.opener = opener
        self.process = None
        self.model = None
        self.port = 0
        self.lock = threading.Lock()

    def base(self, model, timeout=90):
        """The server's address for `model`, starting (or restarting) it
        first; waits until it has loaded the model."""
        with self.lock:
            if self.process is not None and self.process.poll() is None and self.model == str(model):
                return f"http://127.0.0.1:{self.port}"
            self.stop_locked()
            if not os.access(self.program, os.X_OK):
                raise DownloadError("engine")
            self.port = free_port()
            threads = max(1, min(8, (os.cpu_count() or 2) - 1))
            self.process = self.popen([self.program, "-m", str(model), "--host", "127.0.0.1",
                                       "--port", str(self.port), "-c", "4096", "-t", str(threads),
                                       "--no-webui"],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                      stdin=subprocess.DEVNULL)
            self.model = str(model)
            deadline = time.monotonic() + timeout
            url = f"http://127.0.0.1:{self.port}/health"
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise DownloadError("the local model could not be started")
                try:
                    with (self.opener or urllib.request.urlopen)(url, timeout=2) as response:
                        if response.status == 200:
                            return f"http://127.0.0.1:{self.port}"
                except OSError:
                    pass
                time.sleep(0.3)
            self.stop_locked()
            raise DownloadError("the local model did not start in time")

    def stop_locked(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
        self.model = None

    def stop(self):
        with self.lock:
            self.stop_locked()


SERVER_INSTANCE = Server()
