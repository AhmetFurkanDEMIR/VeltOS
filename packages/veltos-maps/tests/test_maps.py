import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from veltos_maps import strings  # noqa: E402
from veltos_maps import app as maps_app  # noqa: E402
from veltos_maps.app import MAPS_URL, trusted_google_url  # noqa: E402
import qtapp  # noqa: E402


def Backend(**kwargs):
    kwargs.setdefault("settings_dir", tempfile.mkdtemp())
    return maps_app.Backend(**kwargs)


class Runner:
    def __init__(self, enabled=False):
        self.enabled = enabled
        self.calls = []
        self.fail_write = False
        self.fail_read = False

    def __call__(self, command, **_kwargs):
        self.calls.append(command)
        if command[0] == "kreadconfig6":
            if self.fail_read:
                return subprocess.CompletedProcess(command, 1, "", "permission denied")
            return subprocess.CompletedProcess(command, 0, "true\n" if self.enabled else "false\n", "")
        if self.fail_write:
            return subprocess.CompletedProcess(command, 1, "", "permission denied")
        self.enabled = command[-1] == "true"
        return subprocess.CompletedProcess(command, 0, "", "")


class MapsBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = qtapp.application()

    def test_english_and_turkish_texts_are_available(self):
        self.assertEqual(strings.text("en", "app_title"), "Maps")
        self.assertEqual(strings.text("tr", "app_title"), "Haritalar")
        self.assertEqual(strings.text("en", "location_on"), "Location on")
        self.assertEqual(strings.text("tr", "location_on"), "Konum açık")
        self.assertEqual(strings.text("en", "my_location"), "My location")
        self.assertEqual(strings.text("tr", "my_location"), "Konumum")

    def test_key_free_search_url_encodes_query(self):
        backend = Backend(lang="en", runner=Runner(), start_url="about:blank")
        backend.search("Café & 42")
        self.assertEqual(backend.mapUrl, f"{MAPS_URL}/search/?api=1&query=Caf%C3%A9+%26+42&hl=en")
        self.assertNotIn("key=", backend.mapUrl)
        previous = backend.mapUrl
        backend.search("  ")
        self.assertEqual(backend.mapUrl, previous)

    def test_only_https_google_origins_are_trusted(self):
        runner = Runner()
        backend = Backend(lang="en", runner=runner, start_url="about:blank")
        self.assertTrue(backend.isGoogleMapsUrl("https://www.google.com/maps"))
        self.assertTrue(backend.isGoogleMapsUrl("https://maps.google.com/"))
        self.assertFalse(backend.isGoogleMapsUrl("http://maps.google.com/"))
        self.assertFalse(backend.isGoogleMapsUrl("https://google.com.attacker.example/"))
        self.assertFalse(backend.isGoogleMapsUrl("https://[not-an-ipv6-address]/"))
        self.assertFalse(backend.isGoogleMapsUrl("https://example.com/"))
        self.assertFalse(backend.canShareLocation("https://www.google.com"))
        backend.setLocationEnabled(True)
        self.assertTrue(backend.canShareLocation("https://maps.google.com"))
        self.assertFalse(backend.canShareLocation("https://example.com"))

    def test_location_is_read_and_written_in_kdeglobals(self):
        runner = Runner(enabled=False)
        backend = Backend(lang="en", runner=runner, start_url="about:blank")
        self.assertFalse(backend.locationEnabled)
        self.assertEqual(runner.calls[0][:4], [
            "kreadconfig6", "--file", "kdeglobals", "--group"])
        backend.setLocationEnabled(True)
        self.assertTrue(backend.locationEnabled)
        self.assertEqual(runner.calls[-1], [
            "kwriteconfig6", "--notify", "--file", "kdeglobals", "--group", "Privacy",
            "--type", "bool", "--key", "LocationServicesEnabled", "true"])
        backend.setLocationEnabled(False)
        self.assertFalse(backend.locationEnabled)

    def test_failed_write_surfaces_an_error_and_keeps_previous_state(self):
        runner = Runner(enabled=False)
        backend = Backend(lang="en", runner=runner, start_url="about:blank")
        runner.fail_write = True
        backend.setLocationEnabled(True)
        self.assertFalse(backend.locationEnabled)
        self.assertIn("permission denied", backend.status)

    def test_current_location_request_requires_opt_in(self):
        calls = []
        backend = Backend(
            lang="en",
            runner=Runner(),
            start_url="about:blank",
            location_provider=lambda _cancel_event: calls.append(True),
        )
        backend.requestCurrentLocation()
        self.assertEqual(calls, [])
        self.assertIn("Turn on location access", backend.status)

    def test_failed_preference_read_cancels_a_pending_location_request(self):
        runner = Runner(enabled=True)
        request_started = threading.Event()
        request_cancelled = []

        def wait_for_cancellation(cancel_event):
            request_cancelled.append(cancel_event)
            request_started.set()
            cancel_event.wait(2)
            return None

        backend = Backend(
            lang="en",
            runner=runner,
            start_url="about:blank",
            location_provider=wait_for_cancellation,
        )
        backend.requestCurrentLocation()
        self.assertTrue(request_started.wait(1))

        runner.fail_read = True
        backend.refreshLocation()

        self.assertFalse(backend.locationEnabled)
        self.assertTrue(request_cancelled[0].is_set())
        backend._location_worker.join(timeout=1)
        self.assertFalse(backend._location_worker.is_alive())

    def test_disabling_location_cancels_a_pending_location_request(self):
        runner = Runner(enabled=True)
        request_started = threading.Event()
        request_cancelled = []

        def wait_for_cancellation(cancel_event):
            request_cancelled.append(cancel_event)
            request_started.set()
            cancel_event.wait(2)
            return None

        backend = Backend(
            lang="en",
            runner=runner,
            start_url="about:blank",
            location_provider=wait_for_cancellation,
        )
        backend.requestCurrentLocation()
        self.assertTrue(request_started.wait(1))

        backend.setLocationEnabled(False)

        self.assertFalse(backend.locationEnabled)
        self.assertTrue(request_cancelled[0].is_set())
        backend._location_worker.join(timeout=1)
        self.assertFalse(backend._location_worker.is_alive())

    def test_google_pages_follow_the_app_language(self):
        self.assertEqual(Backend(lang="tr", runner=Runner()).mapUrl, f"{MAPS_URL}?hl=tr")
        self.assertTrue(Backend(lang="tr", runner=Runner(), start_url="about:blank").acceptLanguage.startswith("tr-TR"))
        self.assertTrue(Backend(lang="en", runner=Runner(), start_url="about:blank").acceptLanguage.startswith("en-US"))

    def test_map_centre_comes_from_googles_address(self):
        self.assertEqual(maps_app.map_centre("https://www.google.com/maps/@41.0082,28.9784,12z?entry=ttu"),
                         (41.0082, 28.9784))
        self.assertEqual(maps_app.map_centre("https://www.google.com/maps/place/X/@-33.86,151.2,15z"),
                         (-33.86, 151.2))
        self.assertIsNone(maps_app.map_centre("https://www.google.com/maps?hl=en"))
        self.assertIsNone(maps_app.map_centre("https://www.google.com/maps/@95.1,10,3z"))

    def test_default_location_is_saved_from_the_map_and_used_when_nothing_is_found(self):
        folder = tempfile.mkdtemp()

        def no_fix(_cancel_event):
            raise TimeoutError("no location within 15 seconds")
        backend = Backend(lang="en", runner=Runner(enabled=True), start_url="about:blank",
                          location_provider=no_fix, set_default=True, settings_dir=folder)
        self.assertTrue(backend.settingDefault)
        self.assertFalse(backend.hasDefaultLocation)
        backend.saveDefaultFromView("https://www.google.com/maps?hl=en")       # no centre yet
        self.assertTrue(backend.settingDefault)
        self.assertEqual(backend.statusKind, "error")
        backend.saveDefaultFromView("https://www.google.com/maps/@39.925533,32.866287,14z")
        self.assertFalse(backend.settingDefault)
        self.assertTrue(backend.hasDefaultLocation)
        saved = json.loads((Path(folder) / "location.json").read_text())
        self.assertEqual(saved, {"latitude": 39.925533, "longitude": 32.866287})
        if os.name == "posix":
            self.assertEqual((Path(folder) / "location.json").stat().st_mode & 0o777, 0o600)
        # "My location" without a fix shows the default location.
        backend._request_location(backend._location_request_id, threading.Event())
        self.app.processEvents()
        self.assertEqual(backend.mapUrl, f"{MAPS_URL}/@39.925533,32.866287,16z?hl=en")
        self.assertIn("default location", backend.status)

    def test_without_a_default_the_failure_says_how_to_set_one(self):
        def no_fix(_cancel_event):
            raise RuntimeError("org.freedesktop.DBus.Error.AccessDenied")
        backend = Backend(lang="en", runner=Runner(enabled=True), start_url="about:blank", location_provider=no_fix)
        backend._request_location(backend._location_request_id, threading.Event())
        self.app.processEvents()
        self.assertEqual(backend.statusKind, "error")
        self.assertIn("default location", backend.status)
        self.assertNotIn("DBus", backend.status)

    def test_privacy_note_is_shown_until_dismissed(self):
        folder = tempfile.mkdtemp()
        self.assertTrue(Backend(lang="en", runner=Runner(), start_url="about:blank", settings_dir=folder)
                        .privacyNoteVisible)
        backend = Backend(lang="en", runner=Runner(), start_url="about:blank", settings_dir=folder)
        backend.dismissPrivacyNote()
        self.assertFalse(Backend(lang="en", runner=Runner(), start_url="about:blank", settings_dir=folder)
                         .privacyNoteVisible)

    def test_a_second_start_raises_the_window_with_its_token(self):
        backend = Backend(lang="en", runner=Runner(), start_url="about:blank")
        raised = []
        backend.raiseRequested.connect(lambda: raised.append(True))
        saved = os.environ.pop("XDG_ACTIVATION_TOKEN", None)
        try:
            maps_app.take_message(backend, json.dumps({"token": "kwin-123", "setDefault": True}).encode())
            self.assertEqual(os.environ.get("XDG_ACTIVATION_TOKEN"), "kwin-123")
        finally:
            os.environ.pop("XDG_ACTIVATION_TOKEN", None)
            if saved is not None:
                os.environ["XDG_ACTIVATION_TOKEN"] = saved
        self.assertEqual(raised, [True])
        self.assertTrue(backend.settingDefault)
        maps_app.take_message(backend, b"not json")
        self.assertEqual(raised, [True, True])


if __name__ == "__main__":
    unittest.main()
