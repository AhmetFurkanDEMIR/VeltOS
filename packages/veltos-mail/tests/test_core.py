"""VeltOS Mail's building blocks: folder names and roles, FETCH answers,
reading and writing messages, the cleaning of HTML mail, providers, the
account, secret and message stores."""

import email
import email.policy
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_mail import accounts, imapcore, mime, store  # noqa: E402


class FolderTests(unittest.TestCase):
    def test_modified_utf7_round_trip(self):
        for name in ("INBOX", "Gönderilmiş Öğeler", "Çöp Kutusu", "été & co", "日本語", "A&B"):
            self.assertEqual(imapcore.decode_mutf7(imapcore.encode_mutf7(name)), name)
        self.assertEqual(imapcore.decode_mutf7("G&APY-nderilmi&AV8- &ANY-&AR8-eler"), "Gönderilmiş Öğeler")
        self.assertEqual(imapcore.encode_mutf7("A&B"), "A&-B")

    def test_list_lines_and_roles(self):
        lines = [b'(\\HasNoChildren) "/" "INBOX"',
                 b'(\\HasChildren \\Noselect) "/" "[Gmail]"',
                 b'(\\HasNoChildren \\Sent) "/" "[Gmail]/Sent Mail"',
                 b'(\\HasNoChildren \\Trash) "/" "[Gmail]/Trash"',
                 b'(\\HasNoChildren \\Drafts) "/" "[Gmail]/Drafts"',
                 b'(\\HasNoChildren \\Junk) "/" "[Gmail]/Spam"',
                 b'(\\HasNoChildren) "/" "Work"',
                 (b'(\\HasNoChildren) "/" {7}', b'Private')]
        folders = imapcore.folders_from_list(lines)
        names = [f["name"] for f in folders]
        self.assertNotIn("[Gmail]", names)                      # \Noselect
        self.assertEqual([f["role"] for f in folders[:5]], ["inbox", "drafts", "sent", "trash", "junk"])
        self.assertIn("Private", names)
        sent = next(f for f in folders if f["role"] == "sent")
        self.assertEqual(sent["leaf"], "Sent Mail")

    def test_roles_from_names_without_flags(self):
        def line(name):
            return ('() "." "' + imapcore.encode_mutf7(name) + '"').encode("ascii")
        lines = [line("INBOX"), line("INBOX.Gönderilmiş"), line("Taslaklar"), line("Spam"), line("Arşiv")]
        roles = {f["name"]: f["role"] for f in imapcore.folders_from_list(lines)}
        self.assertEqual(roles["INBOX"], "inbox")
        self.assertEqual(roles["Taslaklar"], "drafts")
        self.assertEqual(roles["Spam"], "junk")
        self.assertEqual(roles["Arşiv"], "archive")
        self.assertEqual(roles["INBOX.Gönderilmiş"], "sent")

    def test_fetch_answers(self):
        data = [(b'1 (UID 42 RFC822.SIZE 120 BODY[]<0> {5}', b"Hello"),
                b' FLAGS (\\Seen \\Flagged) INTERNALDATE "21-Oct-2026 09:15:00 +0300")',
                (b'2 (UID 43 FLAGS () RFC822.SIZE 9 BODY[]<0> {3}', b"Hey"), b")",
                b"3 (UID 44 FLAGS (\\Answered))"]
        parsed = imapcore.parse_fetch(data)
        self.assertEqual([p["uid"] for p in parsed], [42, 43, 44])
        self.assertEqual(parsed[0]["flags"], ["\\Seen", "\\Flagged"])
        self.assertEqual(parsed[0]["body"], b"Hello")
        self.assertEqual(parsed[0]["internaldate"], "21-Oct-2026 09:15:00 +0300")
        self.assertEqual(parsed[1]["flags"], [])
        self.assertEqual(parsed[2]["flags"], ["\\Answered"])


HTML_MAIL = b"""From: =?utf-8?q?Ay=C5=9Fe_Y=C4=B1lmaz?= <ayse@example.com>
To: Me <me@example.com>
Subject: =?utf-8?b?WWFyxLFua2kgdG9wbGFudMSx?=
Date: Tue, 21 Oct 2026 09:15:00 +0300
Message-ID: <abc@example.com>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="X"

--X
Content-Type: text/html; charset=utf-8

<html><head><style>p{color:red}</style><script>alert(1)</script></head>
<body><p onclick="steal()">Merhaba, <b>yar\xc4\xb1n</b> 10:00'da.</p>
<img src="https://tracker.example/pixel.gif"><img src="cid:logo1">
<a href="javascript:evil()">x</a><iframe src="https://evil"></iframe></body></html>
--X
Content-Type: image/png
Content-ID: <logo1>
Content-Disposition: inline

iVBORw0KGgo=
--X
Content-Type: application/pdf; name="plan.pdf"
Content-Disposition: attachment; filename="plan.pdf"
Content-Transfer-Encoding: base64

JVBERi0xLjQ=
--X--
"""


class MimeTests(unittest.TestCase):
    def test_summary_of_html_mail(self):
        summary = mime.summary(HTML_MAIL)
        self.assertEqual(summary["fromName"], "Ayşe Yılmaz")
        self.assertEqual(summary["fromAddr"], "ayse@example.com")
        self.assertEqual(summary["subject"], "Yarınki toplantı")
        self.assertTrue(summary["preview"].startswith("Merhaba, yarın 10:00"))
        self.assertNotIn("alert", summary["preview"])
        self.assertTrue(summary["attachments"])
        self.assertFalse(summary["other"])
        self.assertGreater(summary["date"], 0)

    def test_newsletters_go_to_other(self):
        news = b"From: News <news@shop.example>\r\nList-Unsubscribe: <mailto:u@shop.example>\r\nSubject: Sale\r\n\r\nx"
        self.assertTrue(mime.summary(news)["other"])
        robot = b"From: GitHub <noreply@github.com>\r\nSubject: CI\r\n\r\nx"
        self.assertTrue(mime.summary(robot)["other"])
        person = b"From: Ali <ali@example.com>\r\nSubject: Hi\r\n\r\nx"
        self.assertFalse(mime.summary(person)["other"])

    def test_html_is_cleaned_and_remote_pictures_blocked(self):
        message = mime.parse_bytes(HTML_MAIL)
        page, blocked = mime.page(message)
        self.assertTrue(blocked)
        for bad in ("<script", "onclick", "javascript:", "<iframe", "tracker.example"):
            self.assertNotIn(bad, page)
        self.assertIn("default-src 'none'", page)
        self.assertNotIn("https:", page.split("img-src")[1].split('"')[0])
        allowed, _ = mime.page(message, allow_remote=True)
        self.assertIn("tracker.example", allowed)
        self.assertNotIn("<script", allowed)

    def test_view_writes_inline_pictures(self):
        message = mime.parse_bytes(HTML_MAIL)
        with tempfile.TemporaryDirectory() as tmp:
            index, _ = mime.write_view(message, tmp)
            text = index.read_text(encoding="utf-8")
            self.assertNotIn("cid:", text)
            self.assertTrue(any(p.name.startswith("logo1") for p in Path(tmp).iterdir()))
        attachments = mime.attachments(message)
        self.assertEqual([a["name"] for a in attachments], ["plan.pdf"])

    def test_plain_text_mail(self):
        plain = b"From: a@b.c\r\nSubject: x\r\n\r\nLine one\r\n> quoted\r\nhttps://veltos.example/page"
        page, blocked = mime.page(mime.parse_bytes(plain))
        self.assertFalse(blocked)
        self.assertIn('<a href="https://veltos.example/page">', page)
        self.assertIn('class="quote"', page)

    def test_build_reply_with_attachment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "notes.txt"
            path.write_text("hello", encoding="utf-8")
            message, recipients = mime.build("Ahmet", "ahmet@example.com", "Ayşe <ayse@example.com>",
                                             "ali@example.com", "boss@example.com", "YNT: Toplantı",
                                             "<p>Tamam <b>görüşürüz</b></p>", [path],
                                             in_reply_to="<abc@example.com>")
        self.assertEqual(recipients, ["ayse@example.com", "ali@example.com", "boss@example.com"])
        self.assertNotIn("Bcc", message)
        self.assertEqual(message["In-Reply-To"], "<abc@example.com>")
        parsed = email.message_from_bytes(message.as_bytes(), policy=email.policy.default)
        self.assertEqual(parsed["Subject"], "YNT: Toplantı")
        self.assertEqual(parsed.get_body(("plain",)).get_content().strip(), "Tamam görüşürüz")
        self.assertEqual([p.get_filename() for p in parsed.iter_attachments()], ["notes.txt"])

    def test_prefix_and_quote(self):
        self.assertEqual(mime.prefixed("Hello", "RE:"), "RE: Hello")
        self.assertEqual(mime.prefixed("RE: Hello", "RE:"), "RE: Hello")
        quoted = mime.quoted(mime.parse_bytes(HTML_MAIL), [("From:", "Ayşe")])
        self.assertIn("<b>From:</b> Ayşe", quoted)
        self.assertNotIn("<script", quoted)

    def test_initials_and_colours(self):
        self.assertEqual(mime.initials("Ayşe Yılmaz"), "AY")
        self.assertEqual(mime.initials("", "ali@example.com"), "A")
        self.assertEqual(mime.avatar_colour("a@b.c"), mime.avatar_colour("A@B.C"))


class AccountTests(unittest.TestCase):
    def test_providers(self):
        key, provider = accounts.provider_for("someone@gmail.com")
        self.assertEqual(key, "gmail")
        self.assertEqual(provider["auth"], "app_password")
        key, provider = accounts.provider_for("someone@hotmail.com")
        self.assertEqual(provider["auth"], "oauth_only")
        settings = accounts.guess_settings("me@gmx.net")[0]
        self.assertEqual(settings["imapHost"], "imap.gmx.net")
        guesses = accounts.guess_settings("me@my-company.example")
        self.assertEqual(guesses[0]["imapHost"], "imap.my-company.example")
        self.assertEqual(len({(g["imapHost"], g["smtpHost"], g["smtpPort"]) for g in guesses}), len(guesses))
        imap, smtp = accounts.discovery("me@my-company.example")
        self.assertEqual([h for h, _p, _s in imap],
                         ["imap.my-company.example", "mail.my-company.example", "my-company.example"])
        self.assertEqual(len(smtp), 6)                       # three hosts, ports 465 and 587
        self.assertEqual(accounts.discovery("me@gmail.com"), ([("imap.gmail.com", 993, "ssl")],
                                                               [("smtp.gmail.com", 465, "ssl")]))
        self.assertTrue(accounts.valid_email("a.b@c.de"))
        self.assertFalse(accounts.valid_email("not an address"))

    def test_account_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "accounts.json"
            store_ = accounts.AccountStore(path)
            account = accounts.new_account("me@gmail.com", "Me", accounts.guess_settings("me@gmail.com")[0])
            store_.add(account)
            store_.set_setting("focusedInbox", False)
            again = accounts.AccountStore(path)
            self.assertEqual(again.accounts[0]["email"], "me@gmail.com")
            self.assertFalse(again.setting("focusedInbox", True))
            self.assertTrue(accounts.saves_sent_itself(account))
            again.remove(account["id"])
            self.assertEqual(accounts.AccountStore(path).accounts, [])

    def test_secrets_file_is_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            secrets = accounts.SecretStore(Path(tmp) / "secrets.json", use_service=False)
            self.assertEqual(secrets.backend, "file")
            secrets.set("a1", "p@ss")
            self.assertEqual(secrets.get("a1"), "p@ss")
            if os.name == "posix":
                mode = stat.S_IMODE(os.stat(Path(tmp) / "secrets.json").st_mode)
                self.assertEqual(mode, 0o600)
            secrets.delete("a1")
            self.assertEqual(secrets.get("a1"), "")


class StoreTests(unittest.TestCase):
    def test_messages_flags_search_contacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = store.Store(Path(tmp) / "mail.sqlite")
            db.set_folders("a", [{"name": "INBOX", "role": "inbox", "leaf": "INBOX", "delimiter": "/", "depth": 0},
                                 {"name": "Trash", "role": "trash", "leaf": "Trash", "delimiter": "/", "depth": 0}])
            db.set_uidvalidity("a", "INBOX", 9)
            items = []
            for uid, (name, other) in enumerate([("Ayşe", False), ("Shop", True), ("Ali", False)], 1):
                items.append({"uid": uid, "fromName": name, "fromAddr": f"{name.lower()}@example.com", "to": "Me",
                              "subject": f"Subject {uid}", "date": 1000 + uid, "preview": "text",
                              "messageId": f"<{uid}>", "attachments": False, "other": other,
                              "flags": ["\\Seen"] if uid == 1 else []})
            db.add_messages("a", "INBOX", 9, items)
            db.update_counts("a")
            inbox = db.folders("a")[0]
            self.assertEqual((inbox["total"], inbox["unread"]), (3, 2))
            self.assertEqual([m["uid"] for m in db.messages("a", "INBOX")], [3, 2, 1])
            self.assertEqual([m["uid"] for m in db.messages("a", "INBOX", tab="focused")], [3, 1])
            self.assertEqual([m["uid"] for m in db.messages("a", "INBOX", tab="other")], [2])
            db.set_field("a", "INBOX", [1], "pinned", True)
            self.assertEqual(db.messages("a", "INBOX")[0]["uid"], 1)
            db.add_messages("a", "INBOX", 9, [dict(items[0], subject="changed")])
            self.assertEqual(db.message("a", "INBOX", 1)["pinned"], 1)     # kept over a refresh
            self.assertEqual([m["uid"] for m in db.search_all("ayşe")], [1])
            self.assertEqual(db.folder_by_role("a", "trash"), "Trash")
            self.assertEqual(len(db.contacts()), 3)
            db.set_uidvalidity("a", "INBOX", 10)                          # renumbered: start again
            self.assertEqual(db.messages("a", "INBOX"), [])
            path = db.body_path("a", "INBOX", 10, 5)
            self.assertEqual(path, db.body_path("a", "INBOX", 10, 5))
            db.forget_account("a")
            self.assertEqual(db.folders("a"), [])
            db.close()


if __name__ == "__main__":
    unittest.main()
