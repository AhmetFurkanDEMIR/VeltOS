"""The sync engine against the in-memory test server (tests/fakeserver.py,
a test double): first sync, new mail on the next sync, flags both ways,
delete into Deleted Items, opening a message, sending with a copy in Sent
Items, and a wrong password."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import PySide6.QtWebEngineQuick  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

import qtapp  # noqa: E402

from fakeserver import FakeImap, FakeSmtp, raw_message  # noqa: E402
from veltos_mail import accounts, mime, store  # noqa: E402


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class SyncTests(unittest.TestCase):
    def setUp(self):
        from veltos_mail import sync
        self.app = qtapp.application()
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        self.folders = {
            "INBOX": {"flags": [], "messages": {
                1: [raw_message(1, "Ayşe <ayse@example.com>", "Toplantı"), {"\\Seen"}],
                2: [raw_message(2, "Shop <news@shop.example>", "Sale",
                                extra_headers="List-Unsubscribe: <mailto:u@shop.example>\r\n"), set()]}},
            "Sent": {"flags": ["\\Sent"], "messages": {}},
            "Trash": {"flags": ["\\Trash"], "messages": {}},
            "Archive": {"flags": ["\\Archive"], "messages": {}},
        }
        self.imap = FakeImap(self.folders)
        self.smtp = FakeSmtp()
        self.accounts = accounts.AccountStore(tmp / "accounts.json")
        self.secrets = accounts.SecretStore(tmp / "secrets.json", use_service=False)
        self.store = store.Store(tmp / "mail.sqlite")
        settings = {"imapHost": "imap.example.com", "imapPort": 993, "imapSecurity": "ssl",
                    "smtpHost": "smtp.example.com", "smtpPort": 465, "smtpSecurity": "ssl"}
        self.account = accounts.new_account("me@example.com", "Me", settings)
        self.accounts.add(self.account)
        self.secrets.set(self.account["id"], "secret")
        self.engine = sync.Engine(self.store, self.accounts, self.secrets,
                                  connection_factory=lambda account: self.imap,
                                  smtp_factory=lambda account: self.smtp)
        self.events = []
        self.engine.newMail.connect(lambda *a: self.events.append(("new",) + a))
        self.engine.bodyReady.connect(lambda *a: self.events.append(("body",) + a))
        self.engine.sendDone.connect(lambda *a: self.events.append(("sent",) + a))
        self.engine.accountState.connect(lambda *a: self.events.append(("state",) + a))
        self.worker = sync.AccountWorker(self.engine, self.account["id"])

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_sync_flags_delete_open_send(self):
        aid = self.account["id"]
        self.worker.job_sync()
        roles = {f["role"]: f["name"] for f in self.store.folders(aid)}
        self.assertEqual(roles["sent"], "Sent")
        self.assertEqual(roles["trash"], "Trash")
        inbox = self.store.messages(aid, "INBOX")
        self.assertEqual(sorted(m["subject"] for m in inbox), ["Sale", "Toplantı"])
        self.assertEqual({m["uid"]: m["other"] for m in inbox}, {1: 0, 2: 1})
        self.assertEqual({m["uid"]: m["seen"] for m in inbox}, {1: 1, 2: 0})
        self.assertEqual(self.store.folders(aid)[0]["unread"], 1)

        # New mail and a flag changed elsewhere arrive with the next sync.
        self.folders["INBOX"]["messages"][3] = [raw_message(3, "Ali <ali@example.com>", "Yeni"), set()]
        self.folders["INBOX"]["messages"][2][1].add("\\Seen")
        self.worker.job_sync(quiet=True)
        self.assertEqual(sorted(m["uid"] for m in self.store.messages(aid, "INBOX")), [1, 2, 3])
        self.assertEqual(self.store.message(aid, "INBOX", 2)["seen"], 1)
        self.assertIn(("new", aid, "Ali", "Yeni", "INBOX"), self.events)

        # Flag from here.
        self.worker.job_flag(folder="INBOX", uids=[3], flag="\\Flagged", add=True)
        self.assertIn("\\Flagged", self.folders["INBOX"]["messages"][3][1])
        self.assertEqual(self.store.message(aid, "INBOX", 3)["flagged"], 1)

        # Opening downloads the whole message and marks it read.
        self.worker.job_body(folder="INBOX", uid=3)
        body = next(e for e in self.events if e[0] == "body")
        self.assertTrue(Path(body[4]).read_bytes().startswith(b"From: Ali"))
        self.assertIn("\\Seen", self.folders["INBOX"]["messages"][3][1])

        # Delete goes to Deleted Items.
        self.worker.job_delete(folder="INBOX", uids=[1])
        self.assertNotIn(1, self.folders["INBOX"]["messages"])
        self.assertEqual(len(self.folders["Trash"]["messages"]), 1)
        self.assertEqual([m["subject"] for m in self.store.messages(aid, "Trash")], ["Toplantı"])

        # Sending: SMTP, then a copy in Sent Items, and "answered" on the original.
        message, recipients = mime.build("Me", "me@example.com", "ali@example.com", "", "", "RE: Yeni",
                                         "<p>Tamam</p>", in_reply_to="<m3@example.com>")
        self.worker.job_send(request_id="r1", message_bytes=message.as_bytes(), recipients=recipients,
                             reply_folder="INBOX", reply_uid=3)
        self.assertEqual(self.smtp.sent[0][1], ["ali@example.com"])
        self.assertIn(("sent", "r1", True, "", ""), self.events)
        self.assertEqual(self.imap.appended[0][0], "Sent")
        self.assertIn("\\Answered", self.folders["INBOX"]["messages"][3][1])
        self.assertEqual([m["subject"] for m in self.store.messages(aid, "Sent")], ["RE: Yeni"])

    def test_wrong_password(self):
        from veltos_mail.imapcore import MailError
        self.secrets.set(self.account["id"], "wrong")
        with self.assertRaises(MailError) as caught:
            self.worker.job_sync()
        self.assertEqual(caught.exception.kind, "auth")


if __name__ == "__main__":
    unittest.main()
