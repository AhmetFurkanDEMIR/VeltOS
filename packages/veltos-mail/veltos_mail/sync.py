"""The background work of VeltOS Mail: one thread per account runs the
account's jobs in order (sign in, folders, new messages, flags, opening a
message, moving, deleting, sending) so the window never waits for a
server. Results come back as Qt signals (queued into the window's thread).
"""

import email
import email.policy
import json
import queue
import socket
import threading
import time

from PySide6.QtCore import QObject, Signal

from . import accounts, mime, outgoing
from .imapcore import ImapConnection, MailError

FIRST_SYNC = {"inbox": 300}      # messages fetched the first time, by folder role
FIRST_SYNC_OTHER = 100
PREVIEW_BYTES = 12288            # the start of each message: headers and the preview
FLAG_WINDOW = 500                # flags are kept in step for the newest messages
POLL_SECONDS = 90
CHECK_TIMEOUT = 10          # per server while adding an account
SMTP_PROBE_TIMEOUT = 5


class Engine(QObject):
    """Signals carry plain values; the backend turns them into the view."""
    accountState = Signal(str, str, str)           # account id, state ("sync", "ok", "error"), detail kind
    foldersChanged = Signal(str)                   # account id
    messagesChanged = Signal(str, str)             # account id, folder
    bodyReady = Signal(str, str, int, str)         # account, folder, uid, path of the .eml
    bodyFailed = Signal(str, str, int, str)
    checkDone = Signal(str, bool, str, str)        # request id, ok, error kind, detail
    sendDone = Signal(str, bool, str, str)         # request id, ok, error kind, detail
    newMail = Signal(str, str, str, str)           # account id, sender, subject, folder

    def __init__(self, store, account_store, secrets, connection_factory=None, smtp_factory=None, parent=None):
        super().__init__(parent)
        self.store = store
        self.accounts = account_store
        self.secrets = secrets
        self.connection_factory = connection_factory
        self.smtp_factory = smtp_factory
        self.workers = {}
        self.oauth_config = outgoing.oauth_config()

    def worker(self, account_id):
        worker = self.workers.get(account_id)
        if worker is None or not worker.is_alive():
            worker = AccountWorker(self, account_id)
            self.workers[account_id] = worker
            worker.start()
        return worker

    def submit(self, account_id, job, **args):
        self.worker(account_id).jobs.put((job, args))

    def sync_all(self):
        for account in self.accounts.accounts:
            self.submit(account["id"], "sync")

    def stop(self, account_id=None):
        for key, worker in list(self.workers.items()):
            if account_id is None or key == account_id:
                worker.jobs.put(("stop", {}))
                if account_id is not None:
                    del self.workers[key]

    def secret_for(self, account):
        """The password, or a fresh OAuth access token."""
        raw = self.secrets.get(account["id"])
        if account.get("auth") != "oauth2":
            return raw
        try:
            tokens = json.loads(raw) if raw else {}
        except ValueError:
            tokens = {}
        if tokens.get("access_token") and tokens.get("expires", 0) > time.time():
            return tokens["access_token"]
        if not tokens.get("refresh_token"):
            raise MailError("auth", "no token")
        provider = accounts.PROVIDERS.get(account.get("provider", ""), {}).get("oauth", "")
        fresh = outgoing.refresh(provider, tokens["refresh_token"], self.oauth_config)
        self.secrets.set(account["id"], json.dumps(fresh))
        return fresh["access_token"]

    # --- checking settings before an account is added (no worker yet) ----------------------------

    def check(self, request_id, account, secret, imap_candidates, smtp_candidates):
        """Signs in to the first IMAP server of the candidates that answers
        (a refused password ends the search: it is wrong everywhere), then
        picks the first SMTP server that takes a connection. Reports
        checkDone with the chosen settings as JSON."""
        def run():
            last = "connect"
            for host, port, security in imap_candidates:
                trial = dict(account, imapHost=host, imapPort=int(port), imapSecurity=security)
                try:
                    connection = ImapConnection(trial, secret, timeout=CHECK_TIMEOUT,
                                                factory=self.connection_factory)
                    connection.folders()
                    connection.close()
                except MailError as error:
                    last = error.kind
                    if error.kind == "auth":
                        break
                    continue
                except Exception:              # anything unexpected: try the next server
                    continue
                smtp = self.find_smtp(smtp_candidates)
                trial.update(smtpHost=smtp[0], smtpPort=int(smtp[1]), smtpSecurity=smtp[2])
                self.checkDone.emit(request_id, True, "", json.dumps(trial))
                return
            self.checkDone.emit(request_id, False, last, "")
        threading.Thread(target=run, daemon=True).start()

    def find_smtp(self, candidates):
        """The first SMTP server that accepts a connection (or the first
        candidate when none does: sending will say so)."""
        if self.smtp_factory is not None:
            return candidates[0]
        for host, port, security in candidates:
            try:
                with socket.create_connection((host, int(port)), timeout=SMTP_PROBE_TIMEOUT):
                    return host, port, security
            except OSError:
                continue
        return candidates[0]


class AccountWorker(threading.Thread):
    def __init__(self, engine, account_id):
        super().__init__(daemon=True)
        self.engine = engine
        self.account_id = account_id
        self.jobs = queue.Queue()
        self.connection = None
        self.last_sync = 0

    @property
    def account(self):
        return self.engine.accounts.get(self.account_id)

    def connect(self):
        if self.connection is not None:
            try:
                self.connection.imap.noop()
                return self.connection
            except Exception:
                self.connection = None
        account = self.account
        if account is None:
            raise MailError("gone")
        self.connection = ImapConnection(account, self.engine.secret_for(account),
                                         factory=self.engine.connection_factory)
        return self.connection

    def run(self):
        while True:
            try:
                job, args = self.jobs.get(timeout=POLL_SECONDS)
            except queue.Empty:
                job, args = "sync", {"quiet": True}
            if job == "stop":
                if self.connection:
                    self.connection.close()
                return
            if self.account is None:
                return
            try:
                getattr(self, "job_" + job)(**args)
            except MailError as error:
                if job == "send":
                    # Sending is SMTP: its failure says nothing about the
                    # account's IMAP connection (the window shows it in the
                    # message being written).
                    self.engine.sendDone.emit(args.get("request_id", ""), False, error.kind, error.detail)
                    continue
                self.connection = None if error.kind in ("connect", "auth") else self.connection
                self.engine.accountState.emit(self.account_id, "error", error.kind)
                if job == "body":
                    self.engine.bodyFailed.emit(self.account_id, args["folder"], args["uid"], error.kind)
            except Exception as error:      # a bug must not end the account's thread
                if job == "send":
                    self.engine.sendDone.emit(args.get("request_id", ""), False, "server", str(error))
                    continue
                self.connection = None
                self.engine.accountState.emit(self.account_id, "error", "connect")
                if job == "body":
                    self.engine.bodyFailed.emit(self.account_id, args["folder"], args["uid"], "server")

    # --- jobs ---------------------------------------------------------------------------------

    def job_sync(self, quiet=False, folder=None):
        store = self.engine.store
        self.engine.accountState.emit(self.account_id, "sync", "")
        connection = self.connect()
        folders = connection.folders()
        store.set_folders(self.account_id, folders)
        self.engine.foldersChanged.emit(self.account_id)
        targets = [f for f in folders if folder is None or f["name"] == folder]
        for info in targets:
            self.sync_folder(connection, info, notify=quiet and info["role"] == "inbox")
        store.update_counts(self.account_id)
        self.engine.foldersChanged.emit(self.account_id)
        self.last_sync = time.time()
        self.engine.accountState.emit(self.account_id, "ok", "")

    def sync_folder(self, connection, info, notify=False):
        store, name = self.engine.store, info["name"]
        selected = connection.select(name, readonly=True)
        validity = selected.get("uidvalidity", 0)
        store.set_uidvalidity(self.account_id, name, validity)
        known = store.known_uids(self.account_id, name)
        on_server = connection.search_uids("ALL") if selected.get("exists") else []
        if not on_server:
            if known:
                store.remove(self.account_id, name, known)
                self.engine.messagesChanged.emit(self.account_id, name)
            return
        newest_known = max(known) if known else 0
        new = [u for u in on_server if u > newest_known]
        if not known:
            new = new[-FIRST_SYNC.get(info["role"], FIRST_SYNC_OTHER):]
        changed = False
        for start in range(0, len(new), 50):
            chunk = new[start:start + 50]
            fetched = connection.fetch(chunk, f"(UID FLAGS RFC822.SIZE INTERNALDATE BODY.PEEK[]<0.{PREVIEW_BYTES}>)")
            items = []
            for item in fetched:
                summary = mime.summary(item["body"], item.get("internaldate", ""))
                summary.update({"uid": item["uid"], "flags": item.get("flags", []), "size": item.get("size", 0)})
                items.append(summary)
            store.add_messages(self.account_id, name, validity, items)
            changed = True
            if notify and known:
                for summary in items:
                    if "\\seen" not in {f.lower() for f in summary["flags"]}:
                        self.engine.newMail.emit(self.account_id, summary["fromName"], summary["subject"], name)
        # Flags and deletions for the newest known messages.
        window = sorted(known)[-FLAG_WINDOW:]
        if window:
            server_set = set(on_server)
            gone = [u for u in window if u not in server_set]
            if gone:
                store.remove(self.account_id, name, gone)
                changed = True
            still = [u for u in window if u in server_set]
            if still:
                flags = {item["uid"]: item.get("flags", []) for item in
                         connection.fetch(still, "(UID FLAGS)")}
                store.set_flags(self.account_id, name, flags)
                changed = True
        store.update_counts(self.account_id, name)
        if changed:
            self.engine.messagesChanged.emit(self.account_id, name)

    def job_body(self, folder, uid, mark_seen=True):
        store = self.engine.store
        validity = store.uidvalidity(self.account_id, folder)
        path = store.body_path(self.account_id, folder, validity, uid)
        if not path.exists():
            connection = self.connect()
            connection.select(folder, readonly=True)
            fetched = connection.fetch([uid], "(UID BODY.PEEK[])")
            if not fetched:
                raise MailError("server", "message gone")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(fetched[0]["body"])
        self.engine.bodyReady.emit(self.account_id, folder, uid, str(path))
        if mark_seen:
            message = store.message(self.account_id, folder, uid)
            if message and not message["seen"]:
                self.job_flag(folder=folder, uids=[uid], flag="\\Seen", add=True)

    def job_flag(self, folder, uids, flag, add):
        connection = self.connect()
        connection.select(folder)
        connection.store_flags(uids, add, flag)
        field = {"\\Seen": "seen", "\\Flagged": "flagged", "\\Answered": "answered"}.get(flag)
        if field:
            self.engine.store.set_field(self.account_id, folder, uids, field, add)
        self.engine.store.update_counts(self.account_id, folder)
        self.engine.messagesChanged.emit(self.account_id, folder)
        self.engine.foldersChanged.emit(self.account_id)

    def job_move(self, folder, uids, target):
        connection = self.connect()
        connection.select(folder)
        connection.move(uids, target)
        self.engine.store.remove(self.account_id, folder, uids)
        self.engine.store.update_counts(self.account_id, folder)
        self.engine.messagesChanged.emit(self.account_id, folder)
        self.job_sync(folder=target)

    def job_delete(self, folder, uids):
        store = self.engine.store
        trash = store.folder_by_role(self.account_id, "trash")
        if trash and folder != trash:
            self.job_move(folder=folder, uids=uids, target=trash)
            return
        connection = self.connect()
        connection.select(folder)
        connection.delete_for_good(uids)
        store.remove(self.account_id, folder, uids)
        store.update_counts(self.account_id, folder)
        self.engine.messagesChanged.emit(self.account_id, folder)
        self.engine.foldersChanged.emit(self.account_id)

    def job_send(self, request_id, message_bytes, recipients, reply_folder="", reply_uid=0):
        account = self.account
        message = email.message_from_bytes(message_bytes, policy=email.policy.default)
        outgoing.send(account, self.engine.secret_for(account), message, recipients,
                      factory=self.engine.smtp_factory)
        self.engine.sendDone.emit(request_id, True, "", "")
        if not accounts.saves_sent_itself(account):
            sent = self.engine.store.folder_by_role(self.account_id, "sent")
            if sent:
                try:
                    self.connect().append(sent, message_bytes)
                except MailError:
                    pass           # sent anyway; only the copy is missing
        if reply_folder and reply_uid:
            try:
                self.job_flag(folder=reply_folder, uids=[reply_uid], flag="\\Answered", add=True)
            except MailError:
                pass
        sent = self.engine.store.folder_by_role(self.account_id, "sent")
        if sent:
            try:
                self.job_sync(folder=sent)
            except MailError:
                pass           # the message is sent; Sent Items shows it with the next sync
