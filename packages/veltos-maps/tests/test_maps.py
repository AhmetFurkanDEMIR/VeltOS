import subprocess
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from veltos_maps import strings  # noqa: E402
from veltos_maps.app import Backend, MAPS_URL, trusted_google_url  # noqa: E402
import qtapp  # noqa: E402


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
        self.assertEqual(backend.mapUrl, f"{MAPS_URL}/search/?api=1&query=Caf%C3%A9+%26+42")
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


if __name__ == "__main__":
    unittest.main()
