"""Tests for the mobile hotspot (veltos_settings/hotspot.py) against a
stand-in for nmcli, iw and ip (fakesystem.HotspotRunner)."""

import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fakesystem import HotspotRunner  # noqa: E402
from veltos_settings import hotspot  # noqa: E402


class HotspotTests(unittest.TestCase):
    def make(self, **kwargs):
        self.runner = HotspotRunner(**kwargs)
        self.config = Path(tempfile.mkdtemp()) / "veltos" / "hotspot.json"
        return hotspot.Hotspot(self.runner, writer=self.runner.write, resolver=self.runner.resolve,
                               user="ayse", config=self.config)

    def test_first_status_proposes_windows_like_defaults_without_writing_a_profile(self):
        h = self.make()
        state = h.status()
        self.assertTrue(state["available"])
        self.assertEqual(state["reason"], "")
        self.assertFalse(state["active"])
        self.assertEqual(state["device"], "wlp2s0")
        self.assertRegex(state["ssid"], r" \d{4}$")
        self.assertTrue(hotspot.valid_password(state["password"]))
        self.assertEqual(len(state["password"]), 8)
        self.assertEqual(state["bands"], ["", "bg", "a"])
        self.assertEqual([s["name"] for s in state["sources"]], ["Wired connection 1"])
        self.assertEqual(state["source"], "2222-bbbb")
        self.assertEqual(self.runner.written, [])
        # The proposal stays the same and only the user can read it.
        self.assertEqual(h.status()["password"], state["password"])
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(os.stat(self.config).st_mode), 0o600)

    def test_start_writes_a_user_owned_shared_access_point_and_brings_it_up(self):
        h = self.make()
        proposed = h.status()
        state = h.start()
        self.assertEqual(state["error"], "")
        self.assertTrue(state["active"])
        settings = self.runner.written[-1]
        self.assertEqual(settings["connection"]["permissions"], ["user:ayse:"])
        self.assertEqual(settings["connection"]["uuid"], hotspot.profile_uuid("ayse"))
        self.assertFalse(settings["connection"]["autoconnect"])
        self.assertEqual(settings["802-11-wireless"]["mode"], "ap")
        self.assertEqual(settings["802-11-wireless"]["ssid"], proposed["ssid"].encode())
        self.assertEqual(settings["ipv4"]["method"], "shared")
        self.assertEqual(settings["802-11-wireless-security"]["key-mgmt"], "wpa-psk")
        self.assertEqual(settings["802-11-wireless-security"]["psk"], proposed["password"])
        self.assertIn(["nmcli", "--wait", "60", "connection", "up", "uuid", hotspot.profile_uuid("ayse"),
                       "ifname", "wlp2s0"], self.runner.commands)
        # The key never appears on a command line.
        self.assertFalse(any(proposed["password"] in " ".join(c) for c in self.runner.commands))

    def test_stop_brings_the_hotspot_down(self):
        h = self.make()
        h.start()
        state = h.stop()
        self.assertFalse(state["active"])
        self.assertIn(["nmcli", "connection", "down", "uuid", hotspot.profile_uuid("ayse")], self.runner.commands)

    def test_connected_devices_with_names_addresses_and_mac(self):
        h = self.make()
        h.start()
        self.runner.stations = [("02:00:00:00:01:00", "10.42.0.126", "ayse-phone"),
                                ("9a:bc:de:f0:12:34", "10.42.0.57", "")]
        clients = h.status()["clients"]
        self.assertEqual(clients, [{"name": "ayse-phone", "ip": "10.42.0.126", "mac": "02:00:00:00:01:00"},
                                   {"name": "", "ip": "10.42.0.57", "mac": "9A:BC:DE:F0:12:34"}])

    def test_without_iw_only_neighbours_that_answer_count(self):
        h = self.make()
        h.start()
        outputs = {("ip", "neigh", "show", "dev", "wlp2s0"):
                   "10.42.0.126 lladdr 02:00:00:00:01:00 REACHABLE \n10.42.0.57 lladdr 9a:bc:de:f0:12:34 STALE \n"}
        base = h.run
        h.run = lambda c, timeout=20, input=None: (127, "") if c[0] == hotspot.IW else \
            (0, outputs[tuple(c)]) if tuple(c) in outputs else base(c, timeout, input)
        self.assertEqual([c["ip"] for c in h.status()["clients"]], ["10.42.0.126"])

    def test_configure_validates_and_restarts_a_running_hotspot(self):
        h = self.make()
        h.start()
        self.assertEqual(h.configure(" Bad", "longenough", "")["error"], "invalid-name")
        self.assertEqual(h.configure("Ayşe'nin ağı", "short", "")["error"], "invalid-password")
        self.assertEqual(h.configure("Ayşe'nin ağı", "şifre1234", "")["error"], "invalid-password")
        before = len(self.runner.commands)
        state = h.configure("Ayşe'nin ağı", "kedi:köpek"[:4] + "12345678", "a")
        self.assertEqual(state["error"], "")
        self.assertEqual(state["ssid"], "Ayşe'nin ağı")
        self.assertEqual(state["band"], "a")
        self.assertEqual(self.runner.written[-1]["802-11-wireless"]["band"], "a")
        self.assertTrue(any(c[3:5] == ["connection", "up"] for c in self.runner.commands[before:]))

    def test_configure_before_the_first_start_keeps_the_choice(self):
        h = self.make()
        h.configure("Office Share", "correct horse", "bg")
        state = h.start()
        self.assertEqual(state["ssid"], "Office Share")
        self.assertEqual(self.runner.written[-1]["802-11-wireless"]["band"], "bg")
        self.assertEqual(self.runner.written[-1]["802-11-wireless-security"]["psk"], "correct horse")

    def test_5ghz_is_offered_only_where_the_card_may_start_a_network(self):
        h = self.make()
        self.assertEqual(h.status()["bands"], ["", "bg", "a"])
        self.runner.no_ir_5ghz = True     # world regulatory domain, as in the dev VM
        self.assertEqual(h.status()["bands"], ["", "bg"])
        h.configure("Net", "password1", "a")
        self.assertEqual(h.status()["band"], "")
        h.start()
        self.assertNotIn("band", self.runner.written[-1]["802-11-wireless"])

    def test_any_band_leaves_the_choice_to_networkmanager(self):
        settings = hotspot.profile_settings("ayse", "Net", "password", "", "wlp2s0")
        self.assertNotIn("band", settings["802-11-wireless"])

    def test_reasons_it_cannot_start(self):
        self.assertEqual(self.make(ethernet=False).status()["reason"], "no-internet")
        self.assertEqual(self.make(ap=False).status()["reason"], "no-ap")
        state = self.make(ethernet=False, wifi_client=True).status()
        self.assertEqual(state["reason"], "same-adapter")
        self.assertEqual(self.make(ethernet=False).start()["error"], "no-internet")
        self.assertEqual(self.runner.written, [])

        def no_wifi(command, timeout=20, input=None):
            if command[3:4] == ["DEVICE,TYPE,STATE,CONNECTION"]:
                return 0, "enp1s0:ethernet:connected:Wired connection 1\n"
            return HotspotRunner()(command)
        h = hotspot.Hotspot(no_wifi, writer=lambda s: True, user="ayse", config=self.config)
        self.assertEqual(h.status()["reason"], "no-wifi")
        self.assertFalse(h.status()["available"])

    def test_wifi_card_on_a_network_says_it_will_disconnect(self):
        state = self.make(wifi_client=True).status()
        self.assertEqual(state["reason"], "")
        self.assertEqual(state["disconnects"], "Home Net")
        # The card's own Wi-Fi connection cannot be the one shared.
        self.assertEqual([s["uuid"] for s in state["sources"]], ["2222-bbbb"])

    def test_a_second_card_hosts_the_hotspot_while_the_first_stays_online(self):
        h = self.make(ethernet=False, wifi_client=True, second_card=True)
        state = h.status()
        self.assertEqual(state["device"], "wlp3s0")
        self.assertEqual(state["disconnects"], "")
        self.assertEqual([s["name"] for s in state["sources"]], ["Home Net"])
        self.assertTrue(h.start()["active"])
        self.assertEqual(self.runner.up_on, "wlp3s0")

    def test_choosing_the_shared_connection_prefers_its_route_until_the_hotspot_stops(self):
        h = self.make(wifi_client=True, second_card=True)
        state = h.status()
        self.assertEqual([s["uuid"] for s in state["sources"]], ["2222-bbbb", "1111-aaaa"])
        h.start()
        state = h.set_source("1111-aaaa")
        self.assertEqual(state["source"], "1111-aaaa")
        self.assertIn(["nmcli", "device", "modify", "wlp2s0", "ipv4.route-metric", "99"], self.runner.commands)
        self.assertEqual(state["sources"][0]["uuid"], "1111-aaaa")
        h.stop()
        self.assertIn(["nmcli", "device", "reapply", "wlp2s0"], self.runner.commands)
        self.assertEqual(self.runner.metrics["wlp2s0"], 600)
        self.assertNotIn("modified", json.loads(self.config.read_text()))

    def test_a_failed_start_says_so(self):
        h = self.make()
        self.runner.fail_up = True
        state = h.start()
        self.assertEqual(state["error"], "start-failed")
        self.assertFalse(state["active"])

    def test_profile_reads_escaped_names(self):
        h = self.make()
        h.configure("Cafe:Free", "password1", "")
        self.assertEqual(h.status()["ssid"], "Cafe:Free")
        h.start()
        self.assertEqual(h.status()["ssid"], "Cafe:Free")

    def test_profile_uuid_is_per_user_and_stable(self):
        self.assertEqual(hotspot.profile_uuid("ayse"), hotspot.profile_uuid("ayse"))
        self.assertNotEqual(hotspot.profile_uuid("ayse"), hotspot.profile_uuid("ali"))

    def test_ptr_reply_is_parsed(self):
        # Answer of dnsmasq 2.91 for 126.0.42.10.in-addr.arpa (compressed name).
        question = b"\x03126\x010\x0242\x0210\x07in-addr\x04arpa\x00\x00\x0c\x00\x01"
        answer = b"\xc0\x0c\x00\x0c\x00\x01\x00\x00\x00\x00\x00\x0e\x0cveltos-phone\x00"
        reply = b"\x12\x34\x85\x80\x00\x01\x00\x01\x00\x00\x00\x00" + question + answer
        self.assertEqual(hotspot.parse_ptr_reply(reply, 0x1234), "veltos-phone")
        self.assertEqual(hotspot.parse_ptr_reply(reply, 0x9999), "")
        refused = b"\x12\x34\x85\x85\x00\x01\x00\x00\x00\x00\x00\x00" + question
        self.assertEqual(hotspot.parse_ptr_reply(refused, 0x1234), "")
        self.assertEqual(hotspot.reverse_name("not an address", "10.42.0.1"), "")

    def test_command_line_prints_json_and_reads_the_key_from_stdin(self):
        h = self.make()
        out = io.StringIO()
        sys.stdout, saved = out, sys.stdout
        try:
            code = hotspot.main(["configure"], h, io.StringIO(json.dumps(
                {"ssid": "Kitchen", "password": "a-long-key", "band": "bg"})))
            hotspot.main(["start"], h)
        finally:
            sys.stdout = saved
        self.assertEqual(code, 0)
        lines = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(lines[0]["ssid"], "Kitchen")
        self.assertTrue(lines[1]["active"])
        self.assertEqual(hotspot.main(["nonsense"], h), 2)


if __name__ == "__main__":
    unittest.main()
