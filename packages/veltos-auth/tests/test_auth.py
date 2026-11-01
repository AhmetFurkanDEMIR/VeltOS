"""The polkit agent's request mapping (agent.py, users.py), the helper
protocol (helper.py) and the prompt window loaded offscreen with a
stand-in helper (dialog.py)."""

import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

from veltos_auth import agent, helper, lockout, strings, users  # noqa: E402

FAKE_HELPER = Path(__file__).resolve().parent / "fake_helper.py"

try:
    from PySide6.QtCore import QObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


class FakeGLib:
    class Variant:
        def __init__(self, signature, value):
            self.signature, self.value = signature, value

        def __eq__(self, other):
            return isinstance(other, FakeGLib.Variant) and (self.signature, self.value) == (other.signature, other.value)


class HelperProtocolTests(unittest.TestCase):
    def test_lines(self):
        self.assertEqual(helper.parse_line("PAM_PROMPT_ECHO_OFF Password: \n"), ("prompt", "Password: ", True))
        self.assertEqual(helper.parse_line("PAM_PROMPT_ECHO_ON Login:"), ("prompt", "Login:", False))
        self.assertEqual(helper.parse_line("PAM_ERROR_MSG Authentication failure\\nTry again"),
                         ("error", "Authentication failure\nTry again", False))
        self.assertEqual(helper.parse_line("PAM_TEXT_INFO Welcome"), ("info", "Welcome", False))
        self.assertEqual(helper.parse_line("SUCCESS"), ("success", "", False))
        self.assertEqual(helper.parse_line("FAILURE\n"), ("failure", "", False))
        self.assertIsNone(helper.parse_line("something else"))

    def test_helper_path(self):
        self.assertEqual(helper.helper_path({"VELTOS_AUTH_HELPER": "/x/helper"}), "/x/helper")
        self.assertTrue(helper.helper_path({}).endswith("polkit-agent-helper-1"))


class RequestTests(unittest.TestCase):
    def test_subject_from_session_or_process(self):
        self.assertEqual(agent.subject({"XDG_SESSION_ID": "3"}, FakeGLib),
                         ("unix-session", {"session-id": FakeGLib.Variant("s", "3")}))
        kind, values = agent.subject({}, FakeGLib)
        self.assertEqual(kind, "unix-process")
        self.assertEqual(values["pid"].value, os.getpid())
        self.assertEqual(values["start-time"].signature, "t")
        self.assertGreater(agent.process_start_time(), 0)

    def test_users_for_identities(self):
        me = os.getuid()
        import pwd
        entry = pwd.getpwuid(me)
        with mock.patch.object(users, "picture_of", return_value="/pic.png"):
            found = users.users_for([("unix-user", {"uid": me}), ("unix-user", {"uid": me}),
                                     ("unix-user", {"uid": 4000000000})])
        self.assertEqual(found, [{"uid": me, "name": entry.pw_name,
                                  "realName": entry.pw_gecos.split(",")[0].strip() or entry.pw_name,
                                  "icon": "/pic.png"}])
        self.assertEqual(users.users_for([("unix-user", {})]), [])

    def test_program_and_description(self):
        self.assertEqual(users.program_name({"program": "/usr/bin/pkexec"}), "pkexec")
        self.assertEqual(users.program_name({"command_line": "/usr/sbin/synaptic --x"}), "synaptic")
        self.assertEqual(users.program_name({}), "")
        folder = Path(tempfile.mkdtemp())
        (folder / "test.policy").write_text(
            '<policyconfig><action id="org.test.do">\n<description>Do the thing</description>\n'
            '<description xml:lang="tr">Şeyi yap</description>\n</action></policyconfig>\n', encoding="utf-8")
        self.assertEqual(users.action_description("org.test.do", (str(folder),)), "Do the thing")
        self.assertEqual(users.action_description("org.test.do", (str(folder),), "tr"), "Şeyi yap")
        self.assertEqual(users.action_description("org.test.other", (str(folder),)), "")

    def test_the_app_that_asked_is_named_with_its_icon(self):
        # The Store installs through ptyrun and pkcon; polkit names pkcon.
        # The prompt shows VeltOS Store and its icon, not PackageKit's
        # package picture (product owner, 2026-10-25).
        root = Path(tempfile.mkdtemp())
        proc, apps = root / "proc", root / "applications"
        apps.mkdir()
        (apps / "veltos-store.desktop").write_text(
            "[Desktop Entry]\nName=VeltOS Store\nName[tr]=VeltOS Mağaza\nIcon=veltos-store\n"
            "[Desktop Action New]\nName=New window\n", encoding="utf-8")
        tree = {"40": (b"pkcon\0-p\0install\0freesweep\0", "39"),
                "39": (b"/usr/bin/python3\0-m\0veltos_store.ptyrun\0pkcon\0", "38"),
                "38": (b"/usr/bin/python3\0/usr/bin/veltos-store\0", "37"),
                "37": (b"sh\0-c\0veltos-store\0", "1")}
        for pid, (cmdline, parent) in tree.items():
            (proc / pid).mkdir(parents=True)
            (proc / pid / "cmdline").write_bytes(cmdline)
            (proc / pid / "stat").write_text(f"{pid} (x y) S {parent} 1 1 0", encoding="utf-8")
        found = users.requesting_app({"polkit.subject-pid": "40"}, "tr", str(proc), (str(apps),))
        self.assertEqual(found, {"name": "VeltOS Mağaza", "icon": "veltos-store"})
        self.assertEqual(users.requesting_app({"polkit.subject-pid": "40"}, "en", str(proc), (str(apps),))["name"],
                         "VeltOS Store")
        self.assertIsNone(users.requesting_app({"polkit.subject-pid": "37"}, "en", str(proc), (str(apps),)))
        self.assertIsNone(users.requesting_app({}, "en", str(proc), (str(apps),)))
        with mock.patch.object(users, "requesting_app", return_value={"name": "VeltOS Store", "icon": "veltos-store"}), \
                mock.patch.object(users, "users_for", return_value=[]):
            request = agent.prompt_request("org.freedesktop.packagekit.package-install", "Install?", "package-x-generic",
                                           {"polkit.subject-pid": "40"}, "c2", [], "en")
        self.assertEqual((request["icon"], request["program"]), ("veltos-store", "VeltOS Store"))

    def test_prompt_request(self):
        with mock.patch.object(users, "users_for", return_value=[{"uid": 1000, "name": "velt"}]):
            request = agent.prompt_request("org.test.do", "Allow?", "icon", {"program": "/bin/x"}, "c1", [], "en")
        self.assertEqual(request["cookie"], "c1")
        self.assertEqual(request["program"], "x")
        self.assertEqual(request["users"][0]["name"], "velt")
        # OK / Cancel, as the product owner asked (2026-10-22).
        self.assertEqual((strings.text("tr", "yes"), strings.text("tr", "no")), ("Tamam", "İptal"))
        self.assertEqual((strings.text("en", "yes"), strings.text("en", "no")), ("OK", "Cancel"))

    def test_polkit_gets_the_session_locale(self):
        # polkit translates its messages into the locale the agent gives it.
        self.assertEqual(strings.polkit_locale({"LANG": "tr_TR.UTF-8", "LANGUAGE": "tr@veltos:tr"}, "tr"),
                         "tr_TR.UTF-8")
        self.assertEqual(strings.polkit_locale({"LANGUAGE": "tr@veltos:tr"}, "tr"), "tr_TR.UTF-8")
        self.assertEqual(strings.polkit_locale({"LANG": "C.UTF-8"}, "en"), "en_US.UTF-8")
        self.assertEqual(strings.polkit_locale({"LC_MESSAGES": "tr_TR.UTF-8", "LANG": "en_US.UTF-8"}, "tr"),
                         "tr_TR.UTF-8")


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class LockoutTests(unittest.TestCase):
    def test_waits_grow_and_the_right_password_resets(self):
        # 3 wrong: 30 s, 3 more: 1 min, then 2 min after every 3 (product
        # owner, 2026-11-01).
        self.assertEqual([lockout.delay_for(n) for n in range(1, 16)],
                         [0, 0, 30, 0, 0, 60, 0, 0, 120, 0, 0, 120, 0, 0, 120])
        path = Path(tempfile.mkdtemp()) / "failures.json"
        self.assertEqual(lockout.remaining(path, now=100), 0)
        self.assertEqual([lockout.failed(path, now=100) for _ in range(3)], [0, 0, 30])
        self.assertEqual(lockout.remaining(path, now=110), 20)
        self.assertEqual(lockout.remaining(path, now=131), 0)
        self.assertEqual([lockout.failed(path, now=200) for _ in range(3)], [0, 0, 60])
        lockout.succeeded(path)
        self.assertEqual(lockout.load(path), {"count": 0, "until": 0})
        self.assertEqual(lockout.state_file({"XDG_RUNTIME_DIR": "/run/user/1000"}),
                         Path("/run/user/1000/veltos/password-failures.json"))


class RememberTests(unittest.TestCase):
    def fake_proc(self, chain):
        """A /proc with pid -> (parent, command line)."""
        root = Path(tempfile.mkdtemp())
        for pid, (parent, command) in chain.items():
            folder = root / str(pid)
            folder.mkdir()
            (folder / "cmdline").write_bytes(command.replace(" ", "\0").encode())
            (folder / "stat").write_text(f"{pid} (x) S {parent} 0 0\n", encoding="utf-8")
        return str(root)

    def test_veltos_ai_and_its_children(self):
        proc = self.fake_proc({300: (200, "pkcon -p install sl"), 200: (100, "/usr/bin/python3 -m veltos_store.ptyrun"),
                               100: (1, "/usr/bin/python3 /usr/bin/veltos-ai"), 400: (1, "/usr/bin/veltos-store")})
        self.assertTrue(agent.from_veltos_ai(300, proc))
        self.assertTrue(agent.from_veltos_ai(100, proc))
        self.assertFalse(agent.from_veltos_ai(400, proc))
        self.assertFalse(agent.from_veltos_ai(999, proc))

    def test_answer_with_a_remembered_password(self):
        command = [sys.executable, str(FAKE_HELPER)]
        self.assertTrue(agent.answer_with("secret", "velt", "cookie-1", command))
        self.assertFalse(agent.answer_with("wrong", "velt", "cookie-1", command))

    def test_ten_minutes_for_veltos_ai_and_retained_actions_only(self):
        a = agent.Agent.__new__(agent.Agent)
        a.implicit = {"org.freedesktop.packagekit.package-install": 4, "org.freedesktop.policykit.exec": 2}
        a.remembered = ("velt", "secret", agent.time.monotonic())
        details = {"polkit.subject-pid": "300"}
        with mock.patch.object(agent, "from_veltos_ai", lambda pid: pid == 300):
            self.assertEqual(a.remembered_for(details, "org.freedesktop.packagekit.package-install"),
                             ("velt", "secret"))
            # pkexec asks every time; other programs never use it.
            self.assertIsNone(a.remembered_for(details, "org.freedesktop.policykit.exec"))
            self.assertIsNone(a.remembered_for({"polkit.subject-pid": "301"},
                                               "org.freedesktop.packagekit.package-install"))
            a.remembered = ("velt", "secret", agent.time.monotonic() - agent.REMEMBER_SECONDS - 1)
            self.assertIsNone(a.remembered_for(details, "org.freedesktop.packagekit.package-install"))
            self.assertIsNone(a.remembered)


class PromptWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["XDG_RUNTIME_DIR"] = tempfile.mkdtemp()
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _type, _ctx, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower() or "warning" in m.lower()]

    def open_prompt(self, lang="en", remember=False):
        from veltos_auth import dialog
        lockout.succeeded()
        self.messages.clear()
        self.out = io.StringIO()
        request = {"cookie": "cookie-1", "action": "org.test.do", "message": "Allow the test?",
                   "icon": "", "details": {"program": "/usr/bin/test"}, "program": "test",
                   "description": "", "users": [{"uid": 1000, "name": "velt", "realName": "Velt User", "icon": ""}]}
        if remember:
            request["remember"] = True
        self.prompt = dialog.Prompt(request, lang=lang, out=self.out,
                                    helper_command=[sys.executable, str(FAKE_HELPER)])
        self.verdicts = []
        self.prompt.finished.connect(self.verdicts.append)
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("auth", self.prompt)
        self.engine.load(QUrl.fromLocalFile(str(dialog.QML_DIR / "Main.qml")))
        self.app.processEvents()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]

    def wait_for_verdict(self):
        import time
        deadline = time.monotonic() + 10
        while not self.verdicts and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.02)

    def tearDown(self):
        self.engine.deleteLater()
        self.app.processEvents()
        self.prompt.deleteLater()
        self.app.processEvents()

    def test_wrong_then_right_password(self):
        self.open_prompt()
        self.assertEqual(self.window.property("title"), "User Account Control")
        self.prompt.submit("nope")
        import time
        deadline = time.monotonic() + 10
        while self.prompt.busy and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.02)
        self.assertFalse(self.prompt.busy)
        self.assertEqual(self.prompt.error, "The password is incorrect. Try again.")
        self.assertEqual(self.verdicts, [])
        self.prompt.submit("secret")
        self.wait_for_verdict()
        self.assertEqual(self.verdicts, ["SUCCESS"])
        self.assertEqual(self.out.getvalue(), "SUCCESS\n")
        self.assertEqual(self.problems(), [])

    def wait_idle(self):
        import time
        deadline = time.monotonic() + 10
        while self.prompt.busy and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.02)

    def test_three_wrong_passwords_wait(self):
        self.open_prompt()
        for _ in range(3):
            self.prompt.submit("nope")
            self.wait_idle()
        self.assertGreater(self.prompt.lockedSeconds, 25)
        self.assertIn("Too many wrong passwords", self.prompt.lockText)
        self.assertEqual(self.window.findChild(QObject, "error").property("text"), self.prompt.lockText)
        self.prompt.submit("secret")                      # ignored while it waits
        self.assertFalse(self.prompt.busy)
        self.assertEqual(self.verdicts, [])
        lockout.succeeded()
        self.assertEqual(self.problems(), [])

    def test_veltos_ai_requests_are_remembered(self):
        self.open_prompt(remember=True)
        self.prompt.submit("secret")
        self.wait_for_verdict()
        self.assertEqual(self.out.getvalue(), "REMEMBER velt secret\nSUCCESS\n")

    def test_cancel_in_turkish(self):
        self.open_prompt("tr")
        self.assertEqual(self.window.property("title"), "Kullanıcı Hesabı Denetimi")
        self.prompt.cancel()
        self.assertEqual(self.out.getvalue(), "CANCELLED\n")
        self.prompt.cancel()                                   # only once
        self.assertEqual(self.out.getvalue(), "CANCELLED\n")
        self.assertEqual(self.problems(), [])


if __name__ == "__main__":
    unittest.main()
