"""IMAP for VeltOS Mail, on Python's imaplib.

What this module adds to imaplib: connecting with SSL or STARTTLS and
signing in (password or XOAUTH2), the folder list with the folders' roles
(Inbox, Drafts, Sent, Deleted, Junk, Archive; RFC 6154 special-use flags,
else the usual names), IMAP's modified UTF-7 folder names (RFC 3501 5.1.3),
and the parsing of FETCH answers into plain dicts.
"""

import base64
import imaplib
import re
import socket
import ssl
import time

TIMEOUT = 25
ROLE_FLAGS = {"\\sent": "sent", "\\drafts": "drafts", "\\trash": "trash", "\\junk": "junk",
              "\\archive": "archive", "\\all": "all", "\\flagged": "flagged"}
# Names that mean a role when the server has no special-use flags
# (English, Turkish and a few common ones).
ROLE_NAMES = {
    "sent": ("sent", "sent items", "sent mail", "sent messages", "gönderilmiş", "gönderilmiş öğeler",
             "gönderilenler", "gönderilen", "gesendet", "envoyés", "inbox.sent"),
    "drafts": ("drafts", "draft", "taslaklar", "taslak", "entwürfe", "brouillons", "inbox.drafts"),
    "trash": ("trash", "deleted items", "deleted messages", "deleted", "bin", "çöp", "çöp kutusu",
              "silinmiş öğeler", "silinenler", "papierkorb", "corbeille", "inbox.trash"),
    "junk": ("junk", "junk email", "junk e-mail", "spam", "bulk mail", "istenmeyen", "istenmeyen e-posta",
             "gereksiz", "gereksiz e-posta", "inbox.junk", "inbox.spam"),
    "archive": ("archive", "archives", "arşiv", "archiv", "inbox.archive"),
}
ROLE_ORDER = ("inbox", "drafts", "sent", "trash", "junk", "archive")
LIST_RE = re.compile(rb'^\((?P<flags>[^)]*)\)\s+(?P<delim>"(?:[^"\\]|\\.)*"|NIL)\s+(?P<name>.+)$')
FETCH_START_RE = re.compile(rb"^\d+\s+\(")


class MailError(Exception):
    """An error to show to the user (kind: "auth", "connect", "server")."""

    def __init__(self, kind, detail=""):
        super().__init__(detail or kind)
        self.kind = kind
        self.detail = detail


# --- modified UTF-7 ------------------------------------------------------------------------------

def decode_mutf7(name):
    """IMAP's folder name encoding: "&AOk-t&AOk-" -> "été"."""
    if isinstance(name, bytes):
        name = name.decode("ascii", "replace")
    out, i = [], 0
    while i < len(name):
        char = name[i]
        if char != "&":
            out.append(char)
            i += 1
            continue
        end = name.find("-", i)
        if end < 0:
            out.append(name[i:])
            break
        chunk = name[i + 1:end]
        if not chunk:
            out.append("&")
        else:
            data = chunk.replace(",", "/")
            data += "=" * (-len(data) % 4)
            try:
                out.append(base64.b64decode(data).decode("utf-16-be"))
            except (ValueError, UnicodeDecodeError):
                out.append(name[i:end + 1])
        i = end + 1
    return "".join(out)


def encode_mutf7(name):
    out, pending = [], []

    def flush():
        if pending:
            data = base64.b64encode("".join(pending).encode("utf-16-be")).decode("ascii").rstrip("=")
            out.append("&" + data.replace("/", ",") + "-")
            pending.clear()
    for char in name:
        if 0x20 <= ord(char) <= 0x7E:
            flush()
            out.append("&-" if char == "&" else char)
        else:
            pending.append(char)
    flush()
    return "".join(out)


def quote(name):
    """A folder name as an IMAP string argument."""
    encoded = encode_mutf7(name)
    return '"' + encoded.replace("\\", "\\\\").replace('"', '\\"') + '"'


# --- folders ------------------------------------------------------------------------------------

def parse_list_line(line):
    """(flags, delimiter, name) of one LIST answer line, or None."""
    if isinstance(line, tuple):              # a literal name: (b'(...) "/" {5}', b'Inbox')
        head, literal = line
        line = head.rsplit(b"{", 1)[0] + b'"' + literal.replace(b'"', b'\\"') + b'"'
    match = LIST_RE.match(line.strip())
    if not match:
        return None
    flags = match.group("flags").decode("ascii", "replace").split()
    delim = match.group("delim")
    delimiter = "" if delim == b"NIL" else delim[1:-1].decode().replace("\\\\", "\\").replace('\\"', '"')
    raw = match.group("name").strip()
    if raw.startswith(b'"') and raw.endswith(b'"'):
        raw = raw[1:-1].replace(b'\\"', b'"').replace(b"\\\\", b"\\")
    return flags, delimiter, decode_mutf7(raw)


def folder_role(flags, name, delimiter):
    if name.upper() == "INBOX":
        return "inbox"
    for flag in flags:
        role = ROLE_FLAGS.get(flag.lower())
        if role:
            return role
    leaf = name.split(delimiter)[-1] if delimiter else name
    for role, names in ROLE_NAMES.items():
        if name.lower() in names or leaf.lower() in names:
            return role
    return ""


def folders_from_list(lines):
    """The selectable folders, with roles; one folder per role (the first)."""
    folders, used = [], set()
    for line in lines:
        parsed = parse_list_line(line)
        if not parsed:
            continue
        flags, delimiter, name = parsed
        lower_flags = {f.lower() for f in flags}
        if "\\noselect" in lower_flags or "\\nonexistent" in lower_flags:
            continue
        role = folder_role(flags, name, delimiter)
        if role in used and role:
            role = ""
        if role in ("all", "flagged"):        # Gmail's All Mail / Starred: kept, shown as folders
            role = role if role not in used else ""
        used.add(role)
        leaf = name.split(delimiter)[-1] if delimiter else name
        folders.append({"name": name, "delimiter": delimiter, "role": role, "leaf": leaf,
                        "depth": name.count(delimiter) if delimiter else 0})
    rank = {role: i for i, role in enumerate(ROLE_ORDER)}
    folders.sort(key=lambda f: (rank.get(f["role"], len(ROLE_ORDER)), f["name"].lower()))
    return folders


# --- FETCH answers ------------------------------------------------------------------------------

def _meta(text):
    out = {}
    match = re.search(rb"UID (\d+)", text)
    if match:
        out["uid"] = int(match.group(1))
    match = re.search(rb"FLAGS \(([^)]*)\)", text)
    if match:
        out["flags"] = [f.decode("ascii", "replace") for f in match.group(1).split()]
    match = re.search(rb"RFC822\.SIZE (\d+)", text)
    if match:
        out["size"] = int(match.group(1))
    match = re.search(rb'INTERNALDATE "([^"]+)"', text)
    if match:
        out["internaldate"] = match.group(1).decode("ascii", "replace")
    return out


def parse_fetch(data):
    """imaplib's FETCH data -> [{"uid", "flags", "size", "internaldate",
    "body"}]. imaplib gives (head, literal) tuples and plain bytes for what
    follows a literal; servers put FLAGS before or after the body."""
    messages, current = [], None
    for item in data or []:
        if item is None:
            continue
        if isinstance(item, tuple):
            head, literal = item[0], item[1]
            if FETCH_START_RE.match(head) or current is None:
                current = {"meta": head, "body": b""}
                messages.append(current)
            else:
                current["meta"] += head
            current["body"] += literal
        else:
            if FETCH_START_RE.match(item):     # a message without a literal (FLAGS only)
                current = {"meta": item, "body": b""}
                messages.append(current)
            elif current is not None:
                current["meta"] += item
    result = []
    for message in messages:
        meta = _meta(message["meta"])
        if "uid" not in meta:
            continue
        meta["body"] = message["body"]
        result.append(meta)
    return result


# --- the connection -----------------------------------------------------------------------------

def xoauth2(user, token):
    return f"user={user}\x01auth=Bearer {token}\x01\x01".encode("utf-8")


class ImapConnection:
    """One signed-in IMAP connection of an account."""

    def __init__(self, account, secret, timeout=TIMEOUT, factory=None):
        self.account = account
        self.capabilities = set()
        context = ssl.create_default_context()
        host, port = account["imapHost"], int(account["imapPort"])
        try:
            if factory is not None:
                self.imap = factory(account)
            elif account.get("imapSecurity") == "starttls":
                self.imap = imaplib.IMAP4(host, port, timeout=timeout)
                self.imap.starttls(ssl_context=context)
            else:
                self.imap = imaplib.IMAP4_SSL(host, port, ssl_context=context, timeout=timeout)
        except (OSError, socket.timeout, ssl.SSLError, imaplib.IMAP4.error) as error:
            raise MailError("connect", str(error)) from error
        try:
            if account.get("auth") == "oauth2":
                self.imap.authenticate("XOAUTH2", lambda _challenge: xoauth2(account["username"], secret))
            else:
                self.imap.login(account["username"], secret)
        except imaplib.IMAP4.error as error:
            self.close()
            raise MailError("auth", str(error)) from error
        except (OSError, ssl.SSLError) as error:
            self.close()
            raise MailError("connect", str(error)) from error
        self.capabilities = {c.upper() for c in getattr(self.imap, "capabilities", ())}

    def close(self):
        try:
            self.imap.logout()
        except Exception:
            pass

    def _ok(self, answer, what):
        status, data = answer
        if status != "OK":
            detail = b" ".join(d for d in data if isinstance(d, bytes)).decode("utf-8", "replace") if data else ""
            raise MailError("server", f"{what}: {detail}")
        return data

    def folders(self):
        try:
            if "SPECIAL-USE" in self.capabilities:
                data = self._ok(self.imap.list('""', "*"), "LIST")
            else:
                data = self._ok(self.imap.list(), "LIST")
        except imaplib.IMAP4.error as error:
            raise MailError("server", str(error)) from error
        return folders_from_list(data)

    def select(self, name, readonly=False):
        try:
            data = self._ok(self.imap.select(quote(name), readonly=readonly), f"SELECT {name}")
        except imaplib.IMAP4.error as error:
            raise MailError("server", str(error)) from error
        info = {"exists": int(data[0]) if data and data[0] else 0}
        for key in ("UIDVALIDITY", "UIDNEXT"):
            try:
                response = self.imap.response(key)[1]
                info[key.lower()] = int(response[0]) if response and response[0] else 0
            except (ValueError, TypeError, IndexError):
                info[key.lower()] = 0
        return info

    def uid(self, command, *args):
        try:
            return self._ok(self.imap.uid(command, *args), f"UID {command}")
        except imaplib.IMAP4.error as error:
            raise MailError("server", str(error)) from error

    def search_uids(self, *criteria):
        data = self.uid("SEARCH", *criteria)
        return [int(x) for x in (data[0] or b"").split()] if data else []

    def fetch(self, uids, items):
        if not uids:
            return []
        return parse_fetch(self.uid("FETCH", ",".join(str(u) for u in uids), items))

    def store_flags(self, uids, add, flag):
        if uids:
            self.uid("STORE", ",".join(str(u) for u in uids), "+FLAGS.SILENT" if add else "-FLAGS.SILENT",
                     f"({flag})")

    def move(self, uids, target):
        if not uids:
            return
        joined = ",".join(str(u) for u in uids)
        if "MOVE" in self.capabilities:
            self.uid("MOVE", joined, quote(target))
            return
        self.uid("COPY", joined, quote(target))
        self.uid("STORE", joined, "+FLAGS.SILENT", "(\\Deleted)")
        self.expunge(uids)

    def expunge(self, uids):
        if "UIDPLUS" in self.capabilities:
            self.uid("EXPUNGE", ",".join(str(u) for u in uids))
        else:
            try:
                self.imap.expunge()
            except imaplib.IMAP4.error as error:
                raise MailError("server", str(error)) from error

    def delete_for_good(self, uids):
        if uids:
            self.uid("STORE", ",".join(str(u) for u in uids), "+FLAGS.SILENT", "(\\Deleted)")
            self.expunge(uids)

    def append(self, folder, raw, flags="(\\Seen)"):
        try:
            self._ok(self.imap.append(quote(folder), flags, imaplib.Time2Internaldate(time.time()),
                                      raw), "APPEND")
        except imaplib.IMAP4.error as error:
            raise MailError("server", str(error)) from error

    def create_folder(self, name):
        try:
            self._ok(self.imap.create(quote(name)), "CREATE")
        except imaplib.IMAP4.error as error:
            raise MailError("server", str(error)) from error
