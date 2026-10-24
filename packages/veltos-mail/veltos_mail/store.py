"""The local copy of VeltOS Mail: folders and message summaries in SQLite
(~/.cache/veltos-mail/mail.sqlite), whole messages as files next to it
once they were opened. Everything here can be fetched again from the
servers; deleting the folder only costs a new download."""

import hashlib
import sqlite3
import threading
from pathlib import Path

from . import accounts

SCHEMA = """
CREATE TABLE IF NOT EXISTS folders (
    account TEXT, name TEXT, role TEXT, leaf TEXT, delimiter TEXT, depth INTEGER,
    uidvalidity INTEGER DEFAULT 0, unread INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
    PRIMARY KEY (account, name));
CREATE TABLE IF NOT EXISTS messages (
    account TEXT, folder TEXT, uid INTEGER, uidvalidity INTEGER,
    from_name TEXT, from_addr TEXT, to_names TEXT, subject TEXT, date INTEGER, preview TEXT,
    seen INTEGER, flagged INTEGER, answered INTEGER, draft INTEGER, attachments INTEGER,
    other INTEGER, size INTEGER, message_id TEXT, pinned INTEGER DEFAULT 0,
    PRIMARY KEY (account, folder, uid));
CREATE INDEX IF NOT EXISTS messages_by_date ON messages (account, folder, date DESC);
"""


class Store:
    def __init__(self, path=None):
        self.path = Path(path or accounts.cache_home() / "veltos-mail/mail.sqlite")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(self.path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        with self.lock:
            self.db.executescript(SCHEMA)
            self.db.commit()

    def body_path(self, account, folder, uidvalidity, uid):
        # A stable name per folder (Python's hash() changes with every start).
        safe = "".join(c if c.isalnum() else "_" for c in folder)[:60]
        digest = hashlib.sha1(folder.encode("utf-8")).hexdigest()[:8]
        return self.path.parent / "bodies" / account / f"{safe}-{digest}" / f"{uidvalidity}-{uid}.eml"

    # --- folders --------------------------------------------------------------------------------

    def set_folders(self, account, folders):
        with self.lock:
            names = {f["name"] for f in folders}
            for row in self.db.execute("SELECT name FROM folders WHERE account=?", (account,)).fetchall():
                if row["name"] not in names:
                    self.db.execute("DELETE FROM folders WHERE account=? AND name=?", (account, row["name"]))
                    self.db.execute("DELETE FROM messages WHERE account=? AND folder=?", (account, row["name"]))
            for f in folders:
                self.db.execute(
                    "INSERT INTO folders (account, name, role, leaf, delimiter, depth) VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(account, name) DO UPDATE SET role=excluded.role, leaf=excluded.leaf, "
                    "delimiter=excluded.delimiter, depth=excluded.depth",
                    (account, f["name"], f["role"], f["leaf"], f["delimiter"], f["depth"]))
            self.db.commit()

    def folders(self, account):
        with self.lock:
            rows = self.db.execute("SELECT * FROM folders WHERE account=?", (account,)).fetchall()
        order = {role: i for i, role in enumerate(("inbox", "drafts", "sent", "trash", "junk", "archive"))}
        folders = [dict(r) for r in rows]
        folders.sort(key=lambda f: (order.get(f["role"], 9), f["name"].lower()))
        return folders

    def folder_by_role(self, account, role):
        with self.lock:
            row = self.db.execute("SELECT name FROM folders WHERE account=? AND role=?", (account, role)).fetchone()
        return row["name"] if row else ""

    def uidvalidity(self, account, folder):
        with self.lock:
            row = self.db.execute("SELECT uidvalidity FROM folders WHERE account=? AND name=?",
                                  (account, folder)).fetchone()
        return row["uidvalidity"] if row else 0

    def set_uidvalidity(self, account, folder, value):
        with self.lock:
            old = self.uidvalidity(account, folder)
            if old and old != value:       # the server renumbered the folder: start again
                self.db.execute("DELETE FROM messages WHERE account=? AND folder=?", (account, folder))
            self.db.execute("UPDATE folders SET uidvalidity=? WHERE account=? AND name=?", (value, account, folder))
            self.db.commit()

    def update_counts(self, account, folder=None):
        with self.lock:
            names = [folder] if folder else [f["name"] for f in self.folders(account)]
            for name in names:
                row = self.db.execute("SELECT COUNT(*) AS total, SUM(seen=0) AS unread FROM messages "
                                      "WHERE account=? AND folder=?", (account, name)).fetchone()
                self.db.execute("UPDATE folders SET total=?, unread=? WHERE account=? AND name=?",
                                (row["total"] or 0, row["unread"] or 0, account, name))
            self.db.commit()

    # --- messages -------------------------------------------------------------------------------

    def known_uids(self, account, folder):
        with self.lock:
            return {r["uid"] for r in self.db.execute("SELECT uid FROM messages WHERE account=? AND folder=?",
                                                      (account, folder))}

    def max_uid(self, account, folder):
        with self.lock:
            row = self.db.execute("SELECT MAX(uid) AS m FROM messages WHERE account=? AND folder=?",
                                  (account, folder)).fetchone()
        return row["m"] or 0

    def add_messages(self, account, folder, uidvalidity, items):
        with self.lock:
            for m in items:
                flags = {f.lower() for f in m.get("flags", [])}
                self.db.execute(
                    "INSERT OR REPLACE INTO messages (account, folder, uid, uidvalidity, from_name, from_addr, "
                    "to_names, subject, date, preview, seen, flagged, answered, draft, attachments, other, size, "
                    "message_id, pinned) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, "
                    "COALESCE((SELECT pinned FROM messages WHERE account=? AND folder=? AND uid=?), 0))",
                    (account, folder, m["uid"], uidvalidity, m["fromName"], m["fromAddr"], m["to"], m["subject"],
                     m["date"], m["preview"], int("\\seen" in flags), int("\\flagged" in flags),
                     int("\\answered" in flags), int("\\draft" in flags), int(m["attachments"]), int(m["other"]),
                     m.get("size", 0), m["messageId"], account, folder, m["uid"]))
            self.db.commit()

    def set_flags(self, account, folder, uid_flags):
        """uid_flags: {uid: [flags]} as the server has them now."""
        with self.lock:
            for uid, flags in uid_flags.items():
                lower = {f.lower() for f in flags}
                self.db.execute("UPDATE messages SET seen=?, flagged=?, answered=? WHERE account=? AND folder=? "
                                "AND uid=?", (int("\\seen" in lower), int("\\flagged" in lower),
                                              int("\\answered" in lower), account, folder, uid))
            self.db.commit()

    def set_field(self, account, folder, uids, field, value):
        if field not in ("seen", "flagged", "answered", "pinned"):
            raise ValueError(field)
        with self.lock:
            for uid in uids:
                self.db.execute(f"UPDATE messages SET {field}=? WHERE account=? AND folder=? AND uid=?",
                                (int(value), account, folder, uid))
            self.db.commit()

    def remove(self, account, folder, uids):
        with self.lock:
            for uid in uids:
                self.db.execute("DELETE FROM messages WHERE account=? AND folder=? AND uid=?", (account, folder, uid))
            self.db.commit()

    def messages(self, account, folder, tab="all", query="", limit=500):
        sql = "SELECT * FROM messages WHERE account=? AND folder=?"
        args = [account, folder]
        if tab == "focused":
            sql += " AND other=0"
        elif tab == "other":
            sql += " AND other=1"
        elif tab == "unread":
            sql += " AND seen=0"
        elif tab == "flagged":
            sql += " AND flagged=1"
        if query:
            sql += " AND (subject LIKE ? OR from_name LIKE ? OR from_addr LIKE ? OR preview LIKE ? OR to_names LIKE ?)"
            like = f"%{query}%"
            args += [like] * 5
        sql += " ORDER BY pinned DESC, date DESC LIMIT ?"
        args.append(limit)
        with self.lock:
            return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def search_all(self, query, limit=200):
        like = f"%{query}%"
        with self.lock:
            rows = self.db.execute(
                "SELECT * FROM messages WHERE subject LIKE ? OR from_name LIKE ? OR from_addr LIKE ? OR preview LIKE ? "
                "OR to_names LIKE ? ORDER BY date DESC LIMIT ?", (like, like, like, like, like, limit)).fetchall()
        return [dict(r) for r in rows]

    def message(self, account, folder, uid):
        with self.lock:
            row = self.db.execute("SELECT * FROM messages WHERE account=? AND folder=? AND uid=?",
                                  (account, folder, uid)).fetchone()
        return dict(row) if row else None

    def contacts(self, limit=300):
        """People the user got mail from (name, address), most frequent first."""
        with self.lock:
            rows = self.db.execute(
                "SELECT from_name, from_addr, COUNT(*) AS n FROM messages WHERE from_addr != '' "
                "GROUP BY lower(from_addr) ORDER BY n DESC LIMIT ?", (limit,)).fetchall()
        return [{"name": r["from_name"], "address": r["from_addr"], "count": r["n"]} for r in rows]

    def close(self):
        with self.lock:
            self.db.close()

    def forget_account(self, account):
        with self.lock:
            self.db.execute("DELETE FROM messages WHERE account=?", (account,))
            self.db.execute("DELETE FROM folders WHERE account=?", (account,))
            self.db.commit()
