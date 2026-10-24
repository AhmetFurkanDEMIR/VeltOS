"""TEST DOUBLES ONLY (never used by VeltOS Mail itself): an in-memory IMAP
server with the part of imaplib's interface sync.py uses, and an SMTP
server that records what was sent. They let the tests run the real
sync code without a network."""

import email
import re


def raw_message(uid, sender, subject, body="Hello there", date="Tue, 21 Oct 2026 09:15:00 +0300",
                extra_headers=""):
    return (f"From: {sender}\r\nTo: me@example.com\r\nSubject: {subject}\r\nDate: {date}\r\n"
            f"Message-ID: <m{uid}@example.com>\r\n{extra_headers}Content-Type: text/plain; charset=utf-8\r\n\r\n"
            f"{body}\r\n").encode("utf-8")


class FakeImap:
    """Folders: {name: {"flags": [...], "messages": {uid: [raw, set(flags)]}}}."""

    def __init__(self, folders, password="secret", capabilities=("IMAP4REV1", "MOVE", "UIDPLUS", "SPECIAL-USE")):
        self.folders = folders
        self.password = password
        self.capabilities = capabilities
        self.selected = None
        self._responses = {}
        self.appended = []
        self.logged_in = False

    # imaplib interface ------------------------------------------------------------------------
    def login(self, user, password):
        import imaplib
        if password != self.password:
            raise imaplib.IMAP4.error("[AUTHENTICATIONFAILED] Invalid credentials")
        self.logged_in = True
        return "OK", [b"Logged in"]

    def authenticate(self, mechanism, callback):
        return self.login("", self.password)

    def logout(self):
        return "BYE", [b""]

    def noop(self):
        return "OK", [b""]

    def list(self, directory='""', pattern="*"):
        lines = []
        for name, folder in self.folders.items():
            flags = " ".join(folder.get("flags", []))
            lines.append(f'({flags}) "/" "{name}"'.encode("utf-8"))
        return "OK", lines

    @staticmethod
    def _unquote(name):
        name = name.strip('"')
        from veltos_mail.imapcore import decode_mutf7
        return decode_mutf7(name)

    def select(self, name, readonly=False):
        name = self._unquote(name)
        if name not in self.folders:
            return "NO", [b"no such folder"]
        self.selected = name
        messages = self.folders[name]["messages"]
        self._responses = {"UIDVALIDITY": [str(self.folders[name].get("validity", 7)).encode()],
                           "UIDNEXT": [str(max(messages, default=0) + 1).encode()]}
        return "OK", [str(len(messages)).encode()]

    def response(self, key):
        return key, self._responses.get(key, [None])

    def expunge(self):
        return "OK", [b""]

    def append(self, folder, flags, date, raw):
        name = self._unquote(folder)
        messages = self.folders[name]["messages"]
        uid = max(messages, default=0) + 1
        messages[uid] = [raw, {"\\Seen"}]
        self.appended.append((name, raw))
        return "OK", [b""]

    def create(self, name):
        self.folders[self._unquote(name)] = {"flags": [], "messages": {}}
        return "OK", [b""]

    def _uids(self, spec):
        messages = self.folders[self.selected]["messages"]
        result = []
        for part in spec.split(","):
            if ":" in part:
                low, high = part.split(":")
                high = max(messages, default=0) if high == "*" else int(high)
                result += [u for u in sorted(messages) if int(low) <= u <= high]
            else:
                result.append(int(part))
        return [u for u in result if u in messages]

    def uid(self, command, *args):
        messages = self.folders[self.selected]["messages"]
        command = command.upper()
        if command == "SEARCH":
            return "OK", [" ".join(str(u) for u in sorted(messages)).encode()]
        if command == "FETCH":
            uids, items = self._uids(args[0]), args[1]
            data = []
            for seq, uid in enumerate(uids, 1):
                raw, flags = messages[uid]
                flag_text = " ".join(sorted(flags))
                if "BODY.PEEK[]" in items:
                    match = re.search(r"<0\.(\d+)>", items)
                    part = raw[:int(match.group(1))] if match else raw
                    head = f"{seq} (UID {uid} RFC822.SIZE {len(raw)} BODY[]{'<0>' if match else ''} {{{len(part)}}}"
                    data.append((head.encode(), part))
                    # Some servers send FLAGS after the literal.
                    data.append(f' FLAGS ({flag_text}) INTERNALDATE "21-Oct-2026 09:15:00 +0300")'.encode())
                else:
                    data.append(f"{seq} (UID {uid} FLAGS ({flag_text}))".encode())
            return "OK", data
        if command == "STORE":
            uids, mode, flags = self._uids(args[0]), args[1], args[2].strip("()").split()
            for uid in uids:
                if mode.startswith("+"):
                    messages[uid][1].update(flags)
                else:
                    messages[uid][1].difference_update(flags)
            return "OK", [b""]
        if command in ("MOVE", "COPY"):
            uids, target = self._uids(args[0]), self._unquote(args[1])
            target_messages = self.folders[target]["messages"]
            for uid in uids:
                new_uid = max(target_messages, default=0) + 1
                target_messages[new_uid] = [messages[uid][0], set(messages[uid][1])]
                if command == "MOVE":
                    del messages[uid]
            return "OK", [b""]
        if command == "EXPUNGE":
            for uid in self._uids(args[0]):
                if "\\Deleted" in messages[uid][1]:
                    del messages[uid]
            return "OK", [b""]
        return "BAD", [b"unknown"]


class FakeSmtp:
    def __init__(self, password="secret"):
        self.password = password
        self.sent = []

    def login(self, user, password):
        import smtplib
        if password != self.password:
            raise smtplib.SMTPAuthenticationError(535, b"bad credentials")

    def send_message(self, message, from_addr=None, to_addrs=None):
        self.sent.append((from_addr, list(to_addrs), message))

    def quit(self):
        pass


def message_text(message):
    if isinstance(message, bytes):
        message = email.message_from_bytes(message)
    return message.as_string()
