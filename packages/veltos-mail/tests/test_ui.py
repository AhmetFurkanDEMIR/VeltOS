"""The VeltOS Mail window offscreen, in English and Turkish: without an
account it shows "Add your account"; with one (synced from the test server
in tests/fakeserver.py, a test double) it lists the messages in date
groups and Focused / Other, opens one in the reading pane (Qt WebEngine),
writes and sends a reply. Any QML warning fails a test."""

import locale
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import qtapp  # noqa: E402  (sets the offscreen platform and WebEngine flags)

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QUrl, qInstallMessageHandler
    from PySide6.QtQml import QQmlApplicationEngine
    import PySide6.QtQuick  # noqa: F401
    import PySide6.QtWebEngineQuick  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

from fakeserver import FakeImap, FakeSmtp, raw_message  # noqa: E402


@unittest.skipUnless(HAVE_QT, "needs PySide6 with QtWebEngine (Build-Depends)")
class MailWindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        cls.app = qtapp.application()
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def setUp(self):
        from veltos_mail import accounts, app, store, sync
        self.messages.clear()
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        self.folders = {
            "INBOX": {"flags": [], "messages": {
                1: [raw_message(1, "Ayşe Yılmaz <ayse@example.com>", "Toplantı", "Yarın 10:00'da görüşelim."), set()],
                2: [raw_message(2, "Shop <news@shop.example>", "Sale",
                                extra_headers="List-Unsubscribe: <mailto:u@shop.example>\r\n"), set()]}},
            "Sent": {"flags": ["\\Sent"], "messages": {}},
            "Trash": {"flags": ["\\Trash"], "messages": {}},
        }
        self.imap, self.smtp = FakeImap(self.folders), FakeSmtp()
        self.accounts = accounts.AccountStore(tmp / "accounts.json")
        self.secrets = accounts.SecretStore(tmp / "secrets.json", use_service=False)
        self.store = store.Store(tmp / "mail.sqlite")
        self.engine = sync.Engine(self.store, self.accounts, self.secrets,
                                  connection_factory=lambda account: self.imap,
                                  smtp_factory=lambda account: self.smtp)
        self.app_module = app
        self.view_dir = tmp / "view"
        self.qml_engine = None

    def load(self):
        self.backend = self.app_module.Backend(lang=self.lang, account_store=self.accounts, mail_store=self.store,
                                               secret_store=self.secrets, engine=self.engine, view_dir=self.view_dir)
        self.qml_engine = QQmlApplicationEngine()
        self.qml_engine.rootContext().setContextProperty("backend", self.backend)
        self.qml_engine.load(QUrl.fromLocalFile(str(self.app_module.QML_DIR / "Main.qml")))
        self.settle()
        self.assertTrue(self.qml_engine.rootObjects(), self.messages)
        self.window = self.qml_engine.rootObjects()[0]

    def add_synced_account(self):
        from veltos_mail import accounts, sync
        settings = {"imapHost": "imap.example.com", "imapPort": 993, "imapSecurity": "ssl",
                    "smtpHost": "smtp.example.com", "smtpPort": 465, "smtpSecurity": "ssl"}
        account = accounts.new_account("me@example.com", "Me", settings)
        self.accounts.add(account)
        self.secrets.set(account["id"], "secret")
        sync.AccountWorker(self.engine, account["id"]).job_sync()
        return account

    def tearDown(self):
        self.engine.stop()
        if self.qml_engine is not None:
            self.qml_engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.store.close()
        self.tmp.cleanup()

    def settle(self, rounds=40):
        for _ in range(rounds):
            self.app.processEvents()

    def wait_for(self, condition, seconds=10):
        deadline = time.time() + seconds
        while time.time() < deadline:
            self.app.processEvents()
            if condition():
                return True
            time.sleep(0.02)
        return False

    def problems(self):
        return [m for m in self.messages if ".qml" in m or "ReferenceError" in m or "TypeError" in m]

    def test_first_start_asks_for_an_account(self):
        self.load()
        self.assertTrue(self.window.property("adding"))
        info = self.backend.providerInfo("someone@gmail.com")
        self.assertEqual(info["auth"], "app_password")
        self.assertFalse(self.backend.providerInfo("nope")["valid"])
        states = []
        self.backend.addAccountState.connect(lambda state, detail: states.append((state, detail)))
        self.backend.addAccount({"email": "someone@hotmail.com", "password": "x"})
        self.assertEqual(states[-1], ("error", "oauth_needed"))
        # Advanced settings, a wrong password, then the right one.
        form = {"email": "me@example.com", "name": "Me", "password": "wrong", "imapHost": "imap.example.com",
                "imapPort": "993", "imapSecurity": "ssl", "smtpHost": "smtp.example.com", "smtpPort": "587",
                "smtpSecurity": "starttls"}
        self.backend.addAccount(form)
        self.assertTrue(self.wait_for(lambda: states[-1][0] != "checking"), states)
        self.assertEqual(states[-1], ("error", "wrong_password"))
        self.backend.addAccount(dict(form, password="secret"))
        self.assertTrue(self.wait_for(lambda: states[-1][0] == "done"), states)
        account = self.accounts.accounts[0]
        self.assertEqual((account["smtpHost"], account["smtpPort"], account["smtpSecurity"]),
                         ("smtp.example.com", 587, "starttls"))
        self.assertEqual(self.secrets.get(account["id"]), "secret")
        self.assertTrue(self.backend.hasAccounts)
        self.settle()
        self.assertEqual(self.problems(), [])

    def test_list_open_reply_send(self):
        self.add_synced_account()
        self.load()
        self.assertFalse(self.window.property("adding"))
        rows = self.backend.messages.rows
        self.assertEqual(rows[0]["kind"], "header")
        focused = [r["subject"] for r in rows if r["kind"] == "message"]
        self.assertEqual(focused, ["Toplantı"])                 # the newsletter is in Other
        self.backend.setTab("other")
        self.assertEqual([r["subject"] for r in self.backend.messages.rows if r["kind"] == "message"], ["Sale"])
        self.backend.setTab("focused")
        tree = self.backend.folderTree
        self.assertEqual(tree[0]["kind"], "section")
        labels = [r["label"] for r in tree if r["kind"] == "folder"]
        inbox_label = "Gelen Kutusu" if self.lang == "tr" else "Inbox"
        self.assertIn(inbox_label, labels)
        self.assertEqual(tree[-1]["kind"], "add")

        message = next(r for r in self.backend.messages.rows if r["kind"] == "message")
        self.backend.openMessage(message["account"], message["folder"], message["uid"])
        self.assertTrue(self.wait_for(lambda: self.backend.reading.get("page")), self.backend.reading)
        self.assertTrue(self.backend.reading["page"].endswith("index.html"))
        self.assertEqual(self.backend.reading["fromName"], "Ayşe Yılmaz")
        self.settle(60)

        self.backend.reply("reply")
        compose = self.backend.compose
        self.assertEqual(compose["to"], "ayse@example.com")
        prefix = "YNT:" if self.lang == "tr" else "RE:"
        self.assertEqual(compose["subject"], f"{prefix} Toplantı")
        self.settle()
        self.assertEqual(self.backend.send(), "")
        self.assertTrue(self.wait_for(lambda: not self.backend.compose), self.backend.compose)
        self.assertEqual(self.smtp.sent[0][1], ["ayse@example.com"])
        self.settle()
        self.assertEqual(self.problems(), [])

    def test_new_mail_needs_a_recipient(self):
        self.add_synced_account()
        self.load()
        self.backend.newMail()
        self.settle()
        self.assertEqual(self.backend.send(), "need_recipient")
        self.backend.discard()
        self.settle()
        self.assertEqual(self.problems(), [])


@unittest.skipUnless(HAVE_QT, "needs PySide6 with QtWebEngine (Build-Depends)")
class TurkishMailWindowTests(MailWindowTests):
    lang = "tr"

    @classmethod
    def setUpClass(cls):
        try:
            locale.setlocale(locale.LC_ALL, "tr_TR.UTF-8")
        except locale.Error:
            pass
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        locale.setlocale(locale.LC_ALL, "C")


@unittest.skipUnless(HAVE_QT, "needs PySide6 with QtWebEngine (Build-Depends)")
class HandOverTests(unittest.TestCase):
    def test_token_travels_with_the_arguments(self):
        # A second start hands its arguments and its activation token to the
        # running Mail, which needs the token to come to the front (Wayland).
        from veltos_mail import app as mail_app
        self.assertEqual(mail_app.handed_over({"args": ["mailto:a@b.c"], "token": "kwin-7"}),
                         (["mailto:a@b.c"], "kwin-7"))
        self.assertEqual(mail_app.handed_over(["mailto:a@b.c"]), (["mailto:a@b.c"], ""))   # older starts


if __name__ == "__main__":
    unittest.main()
