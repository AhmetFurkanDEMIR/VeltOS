"""VeltOS Update without the network: a release as GitHub's API returns it,
the version comparison, the notes per language, the daily check's
decisions with stand-ins, the update steps and the package source."""

import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PKG))

from veltos_update import check, notify, release, source, steps  # noqa: E402

GITHUB = {
    "tag_name": "v1.2", "name": "VeltOS 1.2", "published_at": "2026-12-01T10:00:00Z",
    "html_url": "https://github.com/AhmetFurkanDEMIR/VeltOS/releases/tag/v1.2",
    "body": "## What's new\n\n- VeltOS AI answers faster\n\n<!-- tr -->\n## Yenilikler\n\n- VeltOS AI daha hızlı",
    "assets": [{"name": "Packages.xz", "size": 4000},
               {"name": "VeltOS-1.2-amd64.iso", "size": 2112481280,
                "browser_download_url": "https://github.com/x/releases/download/v1.2/VeltOS-1.2-amd64.iso"}],
}


class ReleaseTests(unittest.TestCase):
    def test_parse_and_notes(self):
        info = release.parse(GITHUB)
        self.assertEqual(info["version"], "1.2")
        self.assertEqual(info["iso"]["size"], 2112481280)
        self.assertEqual(release.notes(info["body"], "en"), "## What's new\n\n- VeltOS AI answers faster")
        self.assertEqual(release.notes(info["body"], "tr"), "## Yenilikler\n\n- VeltOS AI daha hızlı")
        self.assertEqual(release.notes("Only English", "tr"), "Only English")
        # The release's own heading is shown above the notes already.
        self.assertEqual(release.notes("## VeltOS 1.2\n\n### New\n\n- A", "en"), "### New\n\n- A")
        # The ISO's download line of the release text is not for installed PCs.
        body = "- A\n\n**Download:** `V.iso` · SHA-256 `ab`\n\n<!-- tr -->\n\n- B\n\n**İndirme:** `V.iso` · SHA-256 `ab`\n"
        self.assertEqual(release.notes(body, "en"), "- A")
        self.assertEqual(release.notes(body, "tr"), "- B")
        with self.assertRaises(ValueError):
            release.parse({"message": "Not Found"})

    def test_fetch_from_a_file(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "latest.json").write_text(json.dumps(GITHUB), encoding="utf-8")
        info = release.fetch((folder / "latest.json").as_uri())
        self.assertEqual(info["tag"], "v1.2")
        conf = folder / "update.conf"
        conf.write_text("[Update]\nrelease_url = file:///x.json\n")
        self.assertEqual(release.release_url(conf), "file:///x.json")
        self.assertEqual(release.release_url(folder / "none.conf"), release.LATEST_URL)

    def test_versions(self):
        self.assertTrue(release.newer("1.2", "1.1"))
        self.assertTrue(release.newer("v1.10", "1.9"))
        self.assertFalse(release.newer("1.1", "1.1.0"))
        self.assertFalse(release.newer("1.0", "1.1"))
        self.assertTrue(release.newer("1.1", ""))
        self.assertFalse(release.newer("nightly", "1.0"))
        os_release = Path(tempfile.mkdtemp()) / "os-release"
        os_release.write_text('NAME="VeltOS"\nVERSION_ID="1.1"\n')
        self.assertEqual(release.installed_version(os_release), "1.1")


class CheckTests(unittest.TestCase):
    def setUp(self):
        folder = Path(tempfile.mkdtemp())
        self.state, self.conf = folder / "update.json", folder / "update.conf"
        self.told = []

    def notify(self, kind, latest, count):
        self.told.append((kind, latest["version"] if latest else "", count))
        return True

    def check(self, now, latest=GITHUB, installed="1.1", count=0, force=False):
        fetch = (lambda: release.parse(latest)) if latest else self.offline
        return check.run(fetch=fetch, installed=lambda: installed, updates=lambda: (count, 0), notify=self.notify,
                         now=now, state_file=self.state, conf=self.conf, force=force)

    @staticmethod
    def offline():
        raise OSError("no network")

    def test_a_new_release_is_told_once(self):
        day = 86400
        self.assertEqual(self.check(1000 * day), "release")
        self.assertEqual(self.check(1000 * day + 3600), "")             # 20 hours not over: no check
        self.assertEqual(self.check(1001 * day), "")                    # told already
        self.assertEqual(self.told, [("release", "1.2", 0)])
        state = json.loads(self.state.read_text())
        self.assertEqual(state["latest"]["version"], "1.2")
        self.assertEqual(state["notified"], "1.2")

    def test_other_updates_once_a_day_and_offline(self):
        self.assertEqual(self.check(2000 * 86400, installed="1.2", count=3), "updates")
        self.assertEqual(self.check(2000 * 86400 + 72000, installed="1.2", count=3, force=True), "")
        self.assertEqual(self.check(2001 * 86400 + 72000, latest=None, installed="1.2", count=0), "")
        self.assertEqual(self.told, [("updates", "1.2", 3)])

    def test_notifications_off(self):
        self.assertTrue(check.set_notify(False, self.conf))
        self.assertFalse(check.notify_enabled(self.conf))
        self.assertEqual(self.check(3000 * 86400), "")
        self.assertEqual(self.told, [])


class StepTests(unittest.TestCase):
    def test_plan(self):
        self.assertEqual([s for s, _a in steps.plan(True)], ["refresh", "update", "apps"])
        self.assertEqual(steps.plan(False)[1], ("system", ["-p", "install", "veltos-system:amd64"]))

    def test_missing_apps(self):
        depends = "veltos-system\n  Depends: veltos-ai\n  Depends: veltos-newapp\n  Depends: <virtual>\n"

        def runner(command, timeout=120):
            if command[0] == "apt-cache":
                return 0, depends
            return (0, "install ok installed") if command[-1] == "veltos-ai" else (1, "")
        self.assertEqual(steps.missing_apps(runner), ["veltos-newapp"])

    def test_pkcon_output(self):
        self.assertEqual(steps.progress("Percentage:\t42"), ("percent", 42))
        self.assertEqual(steps.progress("Status: \tDownloading packages"), ("status", "Downloading packages"))
        self.assertIsNone(steps.progress("Transaction:\tUpdating packages"))
        out = "Results:\nSecurity    \tlibfoo-1.2-3.amd64 (debian-security)\nNormal \tveltos-ai-1.2.0.all (veltos)\n"
        self.assertEqual(steps.count_updates(out), 2)
        # VeltOS' own packages belong to the release, not to "other updates".
        self.assertEqual(steps.split_updates(out), (1, 1))
        self.assertEqual(steps.split_updates("no results"), (0, 0))


class NotificationTests(unittest.TestCase):
    def test_settings_in_a_unit_of_its_own(self):
        # Not a child of the check's service, which systemd stops with its cgroup.
        calls = []
        notify.open_settings("token-1", run=lambda cmd, **kw: calls.append(cmd))
        self.assertEqual(calls[0][:3], ["systemd-run", "--user", "--collect"])
        self.assertIn("--setenv=XDG_ACTIVATION_TOKEN=token-1", calls[0])
        self.assertEqual(calls[0][-2:], ["veltos-settings", "update"])
        self.assertNotIn("--scope", calls[0])
        self.assertFalse(any("XDG_ACTIVATION" in part for part in notify.settings_command("")))

    def test_texts(self):
        summary, body = notify.message("release", release.parse(GITHUB), 0, "tr")
        self.assertEqual(summary, "VeltOS 1.2 hazır")
        self.assertIn("Dosyalarınız", body)
        self.assertEqual(notify.message("updates", None, 1, "en")[1], "1 update for your PC.")
        self.assertIn("5", notify.message("updates", None, 5, "en")[1])
        self.assertEqual(notify.language({"LANGUAGE": "tr:en_US"}), "tr")
        home = Path(tempfile.mkdtemp())
        (home / ".config").mkdir()
        (home / ".config/plasma-localerc").write_text("[Translations]\nLANGUAGE=tr\n")
        self.assertEqual(notify.language({}, home), "tr")


class Answer:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, size=-1):
        return self.data


class SourceTests(unittest.TestCase):
    """The package source exists only while the newest release has a signed
    index (VeltOS 1.0's release has none: apt update failed, VM 2026-11-02)."""

    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.sources = self.folder / "sources.list.d/veltos.sources"
        self.conf = self.folder / "update.conf"
        self.log = []

    def opener(self, answer):
        def opener(request, timeout=0):
            self.asked = request.full_url
            if isinstance(answer, Exception):
                raise answer
            return Answer(answer)
        return opener

    def main(self, answer, good=True):
        run = lambda *a, **k: type("R", (), {"returncode": 0 if good else 2})()  # noqa: E731
        return source.main(conf=self.conf, sources=self.sources, keyring=Path("/k.gpg"),
                           opener=self.opener(answer), run=run, log=self.log.append)

    def test_on_while_the_release_has_a_signed_index(self):
        self.assertEqual(self.main(b"-----BEGIN PGP SIGNED MESSAGE-----"), 0)
        self.assertEqual(self.asked, source.REPOSITORY + "InRelease")
        text = self.sources.read_text()
        self.assertIn(f"URIs: {source.REPOSITORY}\n", text)
        self.assertIn("Suites: ./\n", text)
        self.assertIn("Signed-By: /k.gpg\n", text)
        self.assertEqual(source.REPOSITORY,
                         "https://github.com/AhmetFurkanDEMIR/VeltOS/releases/latest/download/")
        before = self.sources.stat().st_mtime_ns
        self.main(b"signed")
        self.assertEqual(self.sources.stat().st_mtime_ns, before)       # written once
        self.assertIn("no change", self.log[-1])

    def test_off_while_it_has_none(self):
        self.main(b"signed")
        missing = urllib.error.HTTPError(source.REPOSITORY + "InRelease", 404, "Not Found", {}, None)
        self.assertEqual(self.main(missing), 0)
        self.assertFalse(self.sources.exists())
        self.assertIn("source is off", self.log[-1])

    def test_unchanged_offline_or_badly_signed(self):
        self.main(b"signed")
        self.main(urllib.error.URLError("Temporary failure in name resolution"))
        self.assertTrue(self.sources.exists())
        self.main(urllib.error.HTTPError("x", 503, "Unavailable", {}, None))
        self.assertTrue(self.sources.exists())
        self.sources.unlink()
        self.assertEqual(self.main(b"forged", good=False), 1)
        self.assertFalse(self.sources.exists())

    def test_another_repository_for_tests(self):
        self.conf.write_text("[Update]\nrepository = http://10.0.2.2:8080/repo\n")
        self.main(b"signed")
        self.assertEqual(self.asked, "http://10.0.2.2:8080/repo/InRelease")
        self.assertIn("URIs: http://10.0.2.2:8080/repo/\n", self.sources.read_text())


class FilesTests(unittest.TestCase):
    def test_key_and_timers(self):
        key = (PKG / "data/veltos-archive-keyring.gpg").read_bytes()
        self.assertTrue(key and key[0] & 0x80, "a binary OpenPGP key")
        timer = (PKG / "data/veltos-update-check.timer").read_text()
        self.assertIn("OnUnitActiveSec=24h", timer)
        timer = (PKG / "data/veltos-update-source.timer").read_text()
        self.assertIn("OnBootSec=2min", timer)
        service = (PKG / "data/veltos-update-source.service").read_text()
        self.assertIn("ExecStart=/usr/libexec/veltos/update-source", service)
        self.assertIn("ReadWritePaths=/etc/apt/sources.list.d", service)
        rules = (PKG / "debian/rules").read_text()
        self.assertNotIn("sources.list.d", rules)     # never a fixed file
        self.assertIn("dh_installsystemd veltos-update-source.timer", rules)
        self.assertIn("rm -f /etc/apt/sources.list.d/veltos.sources", (PKG / "debian/postrm").read_text())


if __name__ == "__main__":
    unittest.main()
