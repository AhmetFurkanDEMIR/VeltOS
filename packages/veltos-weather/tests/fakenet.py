"""A stand-in for urllib's opener: answers from tests/data (real Open-Meteo
answers for Istanbul, 2026-10-25) by the URL's host, and records the URLs."""

import io
import urllib.error
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
FILES = {"api.open-meteo.com": "forecast.json", "air-quality-api.open-meteo.com": "air.json",
         "geocoding-api.open-meteo.com": "geocode.json", "archive-api.open-meteo.com": "archive.json"}


class Answer(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class FakeNet:
    def __init__(self, online=True):
        self.online = online
        self.urls = []
        self.headers = []

    def __call__(self, request, timeout=None):
        url = request.full_url
        self.urls.append(url)
        self.headers.append(dict(request.header_items()))
        if not self.online:
            raise urllib.error.URLError("network is unreachable")
        host = url.split("/")[2]
        return Answer((DATA / FILES[host]).read_bytes())
