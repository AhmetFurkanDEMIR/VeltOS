"""VeltOS Mail: e-mail in the layout of Windows 11's new Outlook.

The window (qml/Main.qml): Outlook's blue header with the search box, the
app bar on the left (Mail, Calendar, People), the Home / View / Help tabs
with the simplified ribbon, the folder pane (Favorites, then each account's
folders), the message list (Focused / Other, grouped by date) and the
reading pane; new mail, reply and forward open in the reading pane. The
first start shows Outlook's "Add your account".

This module is the window's backend: it turns the local copy (store.py)
into what the view shows, hands server work to sync.py and writes
messages with mime.py. Account settings live in accounts.py.
"""

import configparser
import datetime
import email
import email.policy
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

from PySide6.QtCore import (Property, QAbstractListModel, QByteArray, QDate, QDateTime, QLocale, QModelIndex, QObject,
                            QTime, QTimer, QUrl, Qt, Signal, Slot)
from PySide6.QtGui import QGuiApplication, QIcon, QRegion
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import accounts, mime, outgoing, store, strings, sync

QML_DIR = Path(__file__).resolve().parent / "qml"
FOLDER_ICONS = {"inbox": "inbox", "drafts": "drafts", "sent": "sent", "trash": "delete", "junk": "junk",
                "archive": "archive", "all": "folder", "flagged": "flag"}
FAVORITE_ROLES = ("inbox", "sent", "drafts")


def kde_value(group, key):
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    for path in (home / "kdeglobals", home / "kdedefaults/kdeglobals", Path("/etc/xdg/kdeglobals")):
        parser = configparser.RawConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
        except (configparser.Error, OSError, UnicodeDecodeError):
            continue
        if parser.has_option(group, key):
            return parser.get(group, key)
    return ""


def text_scale():
    parts = kde_value("General", "font").split(",")
    try:
        return max(1.0, min(2.25, float(parts[1]) / 10)) if len(parts) > 1 else 1.0
    except ValueError:
        return 1.0


def dark_mode():
    for key in ("LookAndFeelPackage", "ColorScheme"):
        value = kde_value("General", key) or kde_value("KDE", key)
        if value:
            return "dark" in value.lower()
    return False


def animations_on():
    try:
        return float(kde_value("KDE", "AnimationDurationFactor") or "1") > 0
    except ValueError:
        return True


def user_full_name():
    try:
        entry = pwd.getpwuid(os.getuid())
    except KeyError:
        return ""
    return entry.pw_gecos.split(",")[0].strip()


def parse_mailto(url):
    """{"to", "cc", "bcc", "subject", "body"} of a mailto: link."""
    parsed = urllib.parse.urlparse(url)
    fields = {"to": urllib.parse.unquote(parsed.path)}
    for key, values in urllib.parse.parse_qs(parsed.query).items():
        key = key.lower()
        if key in ("cc", "bcc", "subject", "body", "to"):
            value = values[0]
            fields[key] = (fields.get(key, "") + ", " + value).strip(", ") if key == "to" else value
    return fields


class MessageModel(QAbstractListModel):
    """The message list: date group headers and messages."""

    revisionChanged = Signal()

    ROLES = ("kind", "key", "label", "uid", "account", "folder", "fromName", "fromAddr", "subject", "preview",
             "time", "seen", "flagged", "pinned", "attachments", "answered", "initials", "colour", "selected",
             "collapsed", "count", "to")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self._revision = 0
        self._roles = {Qt.ItemDataRole.UserRole + i: name.encode() for i, name in enumerate(self.ROLES)}

    @Property(int, notify=revisionChanged)
    def revision(self):
        return self._revision

    def roleNames(self):
        return {k: QByteArray(v) for k, v in self._roles.items()}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role):
        if not index.isValid() or not 0 <= index.row() < len(self.rows):
            return None
        name = self._roles.get(role)
        return self.rows[index.row()].get(name.decode()) if name else None

    def set_rows(self, rows):
        keys = [r["key"] for r in self.rows]
        self._revision += 1
        if keys == [r["key"] for r in rows]:
            self.rows = rows
            if rows:
                self.dataChanged.emit(self.index(0), self.index(len(rows) - 1))
            self.revisionChanged.emit()
            return
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()
        self.revisionChanged.emit()

    @Slot(int, result="QVariantMap")
    def get(self, row):
        return self.rows[row] if 0 <= row < len(self.rows) else {}


class Backend(QObject):
    changed = Signal()                # accounts, folders, settings
    listChanged = Signal()
    readingChanged = Signal()
    composeChanged = Signal()
    composeStarted = Signal()
    statusChanged = Signal()
    addAccountState = Signal(str, str)   # state ("checking", "error", "done"), detail key
    message = Signal(str)

    def __init__(self, lang=None, account_store=None, mail_store=None, secret_store=None, engine=None,
                 view_dir=None, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.locale = QLocale(QLocale.Language.Turkish, QLocale.Country.Turkey) if self.lang == "tr" \
            else QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self.account_store = account_store or accounts.AccountStore()
        self.store = mail_store or store.Store()
        self.secrets = secret_store or accounts.SecretStore()
        self.engine = engine or sync.Engine(self.store, self.account_store, self.secrets)
        self.view_dir = Path(view_dir or tempfile.mkdtemp(prefix="veltos-mail-view-"))
        self.model = MessageModel(self)
        self._dark = dark_mode()
        self._account = ""
        self._folder = ""
        self._tab = "focused"
        self._query = ""
        self._selected = None          # (account, folder, uid)
        self._reading = {}
        self._compose = {}
        self._collapsed = set()
        self._states = {}
        self._pending_add = None
        self._show_pictures = set()
        self.engine.accountState.connect(self._on_state)
        self.engine.foldersChanged.connect(self._on_folders)
        self.engine.messagesChanged.connect(self._on_messages)
        self.engine.bodyReady.connect(self._on_body)
        self.engine.bodyFailed.connect(self._on_body_failed)
        self.engine.checkDone.connect(self._on_check)
        self.engine.sendDone.connect(self._on_sent)
        self.engine.newMail.connect(self._on_new_mail)
        if self.account_store.accounts:
            first = self.account_store.accounts[0]["id"]
            self._account = first
            self._folder = self.store.folder_by_role(first, "inbox") or "INBOX"
        self.refresh_list()

    def start(self):
        self.engine.sync_all()

    # --- texts and look ----------------------------------------------------------------------

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Slot(str, str, result=str)
    def textWith(self, key, value):
        return strings.text(self.lang, key).replace("{value}", value)

    @Property(bool, constant=True)
    def darkMode(self):
        return self._dark

    @Property(float, constant=True)
    def textScale(self):
        return text_scale()

    @Property(bool, constant=True)
    def animations(self):
        return animations_on()

    @Property(QObject, constant=True)
    def messages(self):
        return self.model

    # --- accounts ---------------------------------------------------------------------------

    @Property(bool, notify=changed)
    def hasAccounts(self):
        return bool(self.account_store.accounts)

    @Property("QVariantList", notify=changed)
    def accountList(self):
        return [{"id": a["id"], "email": a["email"], "name": a["name"], "initials": mime.initials(a["name"], a["email"]),
                 "colour": mime.avatar_colour(a["email"]), "state": self._states.get(a["id"], "")}
                for a in self.account_store.accounts]

    @Property(str, constant=True)
    def userName(self):
        return user_full_name()

    @Slot(str, result="QVariantMap")
    def providerInfo(self, email_address):
        """What the add-account page needs to know about an address."""
        address = (email_address or "").strip()
        if not accounts.valid_email(address):
            return {"valid": False}
        key, provider = accounts.provider_for(address)
        auth = provider["auth"] if provider else "password"
        oauth = provider.get("oauth", "") if provider else ""
        return {"valid": True, "provider": key or "", "title": provider["title"] if provider else "",
                "auth": auth, "help": provider.get("help", "") if provider else "",
                "oauthAvailable": bool(oauth) and outgoing.oauth_available(oauth, self.engine.oauth_config)}

    @Slot("QVariantMap")
    def addAccount(self, form):
        """form: name, email, password, and optionally imapHost/Port/Security,
        smtpHost/Port/Security, username (the advanced settings)."""
        address = form.get("email", "").strip()
        if not accounts.valid_email(address):
            self.addAccountState.emit("error", "bad_address")
            return
        if form.get("imapHost"):
            imap = [(form["imapHost"].strip(), int(form.get("imapPort") or 993), form.get("imapSecurity") or "ssl")]
            smtp = [((form.get("smtpHost") or form["imapHost"]).strip(), int(form.get("smtpPort") or 465),
                     form.get("smtpSecurity") or "ssl")]
            provider_key = ""
        else:
            imap, smtp = accounts.discovery(address)
            provider_key = accounts.guess_settings(address)[0]["provider"]
        key, provider = accounts.provider_for(address)
        if provider and provider["auth"] == "oauth_only" and not form.get("imapHost"):
            if not outgoing.oauth_available(provider.get("oauth", ""), self.engine.oauth_config):
                self.addAccountState.emit("error", "oauth_needed")
                return
        name = form.get("name", "").strip() or user_full_name()
        settings = {"provider": provider_key, "imapHost": imap[0][0], "imapPort": imap[0][1],
                    "imapSecurity": imap[0][2], "smtpHost": smtp[0][0], "smtpPort": smtp[0][1],
                    "smtpSecurity": smtp[0][2]}
        account = accounts.new_account(address, name, settings, username=form.get("username", ""))
        self._pending_add = {"form": form, "account": account}
        self.addAccountState.emit("checking", "")
        self.engine.check("add", account, form.get("password", ""), imap, smtp)

    @Slot(str, bool, str, str)
    def _on_check(self, request_id, ok, kind, detail):
        pending = self._pending_add
        if request_id != "add" or pending is None:
            return
        self._pending_add = None
        if not ok:
            key, provider = accounts.provider_for(pending["form"]["email"])
            if kind == "auth" and provider and provider["auth"] == "app_password":
                self.addAccountState.emit("error", "app_password_error")
            else:
                self.addAccountState.emit("error", {"auth": "wrong_password"}.get(kind, "no_server"))
            return
        account = json.loads(detail)
        self.secrets.set(account["id"], pending["form"].get("password", ""))
        self.account_store.add(account)
        self._account = account["id"]
        self._folder = "INBOX"
        self.changed.emit()
        self.refresh_list()
        self.engine.submit(account["id"], "sync")
        self.addAccountState.emit("done", "")

    @Slot()
    def cancelAddAccount(self):
        self._pending_add = None

    @Slot(str)
    def removeAccount(self, account_id):
        self.engine.stop(account_id)
        self.account_store.remove(account_id)
        self.secrets.delete(account_id)
        self.store.forget_account(account_id)
        if self._account == account_id:
            first = self.account_store.accounts[0]["id"] if self.account_store.accounts else ""
            self._account = first
            self._folder = (self.store.folder_by_role(first, "inbox") or "INBOX") if first else ""
            self._clear_reading()
        self.changed.emit()
        self.refresh_list()

    @Slot(str, str)
    def setSignature(self, account_id, text):
        self.account_store.update(account_id, signature=text)
        self.changed.emit()

    @Slot(str, result=str)
    def signature(self, account_id):
        account = self.account_store.get(account_id)
        return account.get("signature", "") if account else ""

    # --- settings -----------------------------------------------------------------------------

    @Property(bool, notify=changed)
    def focusedInbox(self):
        return bool(self.account_store.setting("focusedInbox", True))

    @Slot(bool)
    def setFocusedInbox(self, on):
        self.account_store.set_setting("focusedInbox", bool(on))
        self.changed.emit()
        self.refresh_list()

    @Property(bool, notify=changed)
    def showPreview(self):
        return bool(self.account_store.setting("showPreview", True))

    @Slot(bool)
    def setShowPreview(self, on):
        self.account_store.set_setting("showPreview", bool(on))
        self.changed.emit()

    @Property(bool, notify=changed)
    def showAvatars(self):
        return bool(self.account_store.setting("showAvatars", True))

    @Slot(bool)
    def setShowAvatars(self, on):
        self.account_store.set_setting("showAvatars", bool(on))
        self.changed.emit()

    @Property(bool, notify=changed)
    def folderPaneOpen(self):
        return bool(self.account_store.setting("folderPane", True))

    @Slot()
    def toggleFolderPane(self):
        self.account_store.set_setting("folderPane", not self.folderPaneOpen)
        self.changed.emit()

    # --- folders --------------------------------------------------------------------------------

    def folder_label(self, folder):
        role = folder.get("role", "")
        if role in ("inbox", "drafts", "sent", "trash", "junk", "archive"):
            return self.text("folder_" + role)
        return folder.get("leaf") or folder["name"]

    @Property("QVariantList", notify=changed)
    def folderTree(self):
        """Rows of the folder pane: "section" headers, "folder" rows and
        "add" (Add account)."""
        rows = []
        multi = len(self.account_store.accounts) > 1
        favourites = []
        for account in self.account_store.accounts:
            for folder in self.store.folders(account["id"]):
                if folder["role"] in FAVORITE_ROLES:
                    favourites.append((account, folder))
        if favourites:
            rows.append({"kind": "section", "key": "fav", "label": self.text("favorites"),
                         "collapsed": "fav" in self._collapsed})
            if "fav" not in self._collapsed:
                order = {r: i for i, r in enumerate(FAVORITE_ROLES)}
                favourites.sort(key=lambda af: (order[af[1]["role"]], self.account_store.accounts.index(af[0])))
                for account, folder in favourites:
                    label = self.folder_label(folder)
                    rows.append(self._folder_row(account, folder, label + (f" · {account['email']}" if multi else ""),
                                                 0, "fav"))
        for account in self.account_store.accounts:
            key = "acc:" + account["id"]
            rows.append({"kind": "section", "key": key, "label": account["email"], "collapsed": key in self._collapsed,
                         "state": self._states.get(account["id"], ""), "account": account["id"]})
            if key in self._collapsed:
                continue
            for folder in self.store.folders(account["id"]):
                rows.append(self._folder_row(account, folder, self.folder_label(folder),
                                             folder["depth"] if not folder["role"] else 0, key))
        rows.append({"kind": "add", "key": "add", "label": self.text("add_account")})
        return rows

    def _folder_row(self, account, folder, label, depth, section):
        return {"kind": "folder", "key": section + "|" + account["id"] + "|" + folder["name"], "label": label,
                "account": account["id"], "folder": folder["name"], "role": folder["role"],
                "icon": FOLDER_ICONS.get(folder["role"], "folder"), "unread": folder["unread"],
                "total": folder["total"], "depth": depth,
                "current": account["id"] == self._account and folder["name"] == self._folder,
                "showTotal": folder["role"] in ("drafts",)}

    @Slot(str)
    def toggleSection(self, key):
        self._collapsed ^= {key}
        self.changed.emit()

    @Property(str, notify=listChanged)
    def currentAccount(self):
        return self._account

    @Property(str, notify=listChanged)
    def currentFolder(self):
        return self._folder

    @Property(str, notify=listChanged)
    def currentRole(self):
        for folder in self.store.folders(self._account) if self._account else []:
            if folder["name"] == self._folder:
                return folder["role"]
        return "inbox" if self._folder.upper() == "INBOX" else ""

    @Property(str, notify=listChanged)
    def currentFolderLabel(self):
        if self._query:
            return self.text("search_results")
        for folder in self.store.folders(self._account) if self._account else []:
            if folder["name"] == self._folder:
                return self.folder_label(folder)
        return self.text("folder_inbox")

    @Slot(str, str)
    def selectFolder(self, account_id, folder):
        self._account, self._folder, self._query = account_id, folder, ""
        self._tab = "focused" if self.focusedInbox else "all"
        self._clear_reading()
        self.changed.emit()
        self.refresh_list()
        self.engine.submit(account_id, "sync", folder=folder)

    @Slot(result="QVariantList")
    def moveTargets(self):
        """Folders a message of the current account can go to."""
        return [{"folder": f["name"], "label": self.folder_label(f), "icon": FOLDER_ICONS.get(f["role"], "folder")}
                for f in self.store.folders(self._account) if f["name"] != self._folder]

    # --- the message list -----------------------------------------------------------------------

    @Property(str, notify=listChanged)
    def tab(self):
        return self._tab

    @Slot(str)
    def setTab(self, tab):
        self._tab = tab
        self.refresh_list()

    @Property(bool, notify=listChanged)
    def tabsShown(self):
        return self.focusedInbox and self.currentRole == "inbox" and not self._query

    @Property(str, notify=listChanged)
    def query(self):
        return self._query

    @Slot(str)
    def search(self, text):
        self._query = text.strip()
        self.refresh_list()

    @Property(int, notify=listChanged)
    def listCount(self):
        return sum(1 for r in self.model.rows if r["kind"] == "message")

    @Property(bool, notify=statusChanged)
    def syncing(self):
        return any(state == "sync" for state in self._states.values())

    @Property(str, notify=statusChanged)
    def accountError(self):
        for account in self.account_store.accounts:
            if self._states.get(account["id"]) in ("error:auth", "error:connect"):
                return self.textWith("error_" + self._states[account["id"]].split(":")[1], account["email"])
        return ""

    def group_of(self, timestamp, today):
        day = datetime.datetime.fromtimestamp(timestamp).date() if timestamp else today
        delta = (today - day).days
        if delta <= 0:
            return "today"
        if delta == 1:
            return "yesterday"
        week_start = today - datetime.timedelta(days=today.weekday())
        if day >= week_start:
            return "this_week"
        if day >= week_start - datetime.timedelta(days=7):
            return "last_week"
        if day.year == today.year and day.month == today.month:
            return "this_month"
        last_month = (today.replace(day=1) - datetime.timedelta(days=1))
        if day.year == last_month.year and day.month == last_month.month:
            return "last_month"
        return "older"

    def list_time(self, timestamp, today):
        if not timestamp:
            return ""
        moment = datetime.datetime.fromtimestamp(timestamp)
        time_text = self.locale.toString(QTime(moment.hour, moment.minute), QLocale.FormatType.ShortFormat)
        if moment.date() == today:
            return time_text
        if (today - moment.date()).days < 7:
            day = self.locale.dayName(moment.isoweekday(), QLocale.FormatType.ShortFormat)
            return f"{day} {time_text}"
        return self.locale.toString(QDate(moment.year, moment.month, moment.day), QLocale.FormatType.ShortFormat)

    def refresh_list(self):
        today = datetime.date.today()
        if not self._account and not self._query:
            self.model.set_rows([])
            self.listChanged.emit()
            return
        if self._query:
            found = self.store.search_all(self._query)
        else:
            tab = self._tab if self.tabsShown else "all"
            found = self.store.messages(self._account, self._folder, tab=tab)
        rows, last_group, pinned_done = [], None, False
        for message in found:
            group = "pinned" if message["pinned"] and not self._query else self.group_of(message["date"], today)
            if group != last_group:
                rows.append({"kind": "header", "key": "h:" + group, "label": self.text("group_" + group),
                             "collapsed": group in self._collapsed})
                last_group = group
            if group in self._collapsed:
                continue
            selected = self._selected == (message["account"], message["folder"], message["uid"])
            rows.append({"kind": "message", "key": f"{message['account']}|{message['folder']}|{message['uid']}",
                         "uid": message["uid"], "account": message["account"], "folder": message["folder"],
                         "fromName": message["from_name"] or message["from_addr"], "fromAddr": message["from_addr"],
                         "to": message["to_names"], "subject": message["subject"] or self.text("no_subject"),
                         "preview": message["preview"], "time": self.list_time(message["date"], today),
                         "seen": bool(message["seen"]), "flagged": bool(message["flagged"]),
                         "pinned": bool(message["pinned"]), "attachments": bool(message["attachments"]),
                         "answered": bool(message["answered"]),
                         "initials": mime.initials(message["from_name"], message["from_addr"]),
                         "colour": mime.avatar_colour(message["from_addr"]), "selected": selected})
        self.model.set_rows(rows)
        self.listChanged.emit()

    @Slot(str)
    def toggleGroup(self, group):
        self._collapsed ^= {group}
        self.refresh_list()

    # --- reading ----------------------------------------------------------------------------------

    @Property("QVariantMap", notify=readingChanged)
    def reading(self):
        return self._reading

    def _clear_reading(self):
        self._selected = None
        self._reading = {}
        self.readingChanged.emit()

    @Slot(str, str, int)
    def openMessage(self, account_id, folder, uid):
        self._selected = (account_id, folder, uid)
        row = self.store.message(account_id, folder, uid)
        if row is None:
            return
        if self._compose:
            self._compose = {}
            self.composeChanged.emit()
        moment = QDateTime.fromSecsSinceEpoch(int(row["date"])) if row["date"] else None
        self._reading = {"account": account_id, "folder": folder, "uid": uid, "loading": True,
                         "subject": row["subject"] or self.text("no_subject"),
                         "fromName": row["from_name"] or row["from_addr"], "fromAddr": row["from_addr"],
                         "initials": mime.initials(row["from_name"], row["from_addr"]),
                         "colour": mime.avatar_colour(row["from_addr"]), "to": row["to_names"], "cc": "",
                         "date": self.locale.toString(moment, QLocale.FormatType.ShortFormat) if moment else "",
                         "dateLong": (self.locale.toString(moment.date(), "ddd ") +
                                      self.locale.toString(moment, QLocale.FormatType.ShortFormat)) if moment else "",
                         "flagged": bool(row["flagged"]), "seen": True, "pinned": bool(row["pinned"]),
                         "attachments": [], "page": "", "blocked": False, "failed": ""}
        self.readingChanged.emit()
        self.refresh_list()
        self.engine.submit(account_id, "body", folder=folder, uid=uid)

    @Slot(str, str, int, str)
    def _on_body(self, account_id, folder, uid, path):
        if self._selected != (account_id, folder, uid):
            return
        self._show_body(Path(path))

    def _show_body(self, path):
        account_id, folder, uid = self._selected
        try:
            raw = path.read_bytes()
        except OSError:
            self._on_body_failed(account_id, folder, uid, "server")
            return
        message = mime.parse_bytes(raw)
        allow = (account_id, folder, uid) in self._show_pictures
        target = self.view_dir / f"{abs(hash((account_id, folder, uid, allow)))}"
        index, blocked = mime.write_view(message, target, dark=self._dark, allow_remote=allow)
        cc = ", ".join(mime.display_name(n, a) for n, a in mime.addresses(message.get("Cc")))
        to = ", ".join(mime.display_name(n, a) for n, a in mime.addresses(message.get("To")))
        self._reading.update({"loading": False, "page": QUrl.fromLocalFile(str(index)).toString(),
                              "blocked": blocked and not allow, "cc": cc, "to": to,
                              "attachments": [dict(a, sizeText=self.size_text(a["size"]))
                                              for a in mime.attachments(message)],
                              "raw": str(path)})
        self.readingChanged.emit()

    @Slot(str, str, int, str)
    def _on_body_failed(self, account_id, folder, uid, kind):
        if self._selected == (account_id, folder, uid):
            self._reading.update({"loading": False, "failed": kind})
            self.readingChanged.emit()

    def long_date(self, timestamp):
        """Outlook's date in a quoted message: "Saturday, October 24, 2026 5:54 AM"."""
        if not timestamp:
            return ""
        moment = QDateTime.fromSecsSinceEpoch(int(timestamp))
        return (self.locale.toString(moment.date(), QLocale.FormatType.LongFormat) + " "
                + self.locale.toString(moment.time(), QLocale.FormatType.ShortFormat))

    def size_text(self, size):
        for unit in ("B", "KB", "MB"):
            if size < 1024:
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}".replace(".", "," if self.lang == "tr" else ".")
            size /= 1024
        return f"{size:.1f} GB"

    @Slot()
    def showPictures(self):
        if self._selected:
            self._show_pictures.add(self._selected)
            raw = self._reading.get("raw")
            if raw:
                self._show_body(Path(raw))

    def _current_message(self):
        raw = self._reading.get("raw")
        if not raw:
            return None
        try:
            return email.message_from_bytes(Path(raw).read_bytes(), policy=email.policy.compat32)
        except OSError:
            return None

    @Slot(int)
    def openAttachment(self, index):
        message = self._current_message()
        if message is None:
            return
        info = next((a for a in mime.attachments(message) if a["index"] == index), None)
        if info is None:
            return
        target = self.view_dir / "files" / re.sub(r"[/\\]", "_", info["name"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if mime.save_attachment(message, index, target):
            subprocess.Popen(["xdg-open", str(target)], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @Slot(int)
    def saveAttachment(self, index):
        message = self._current_message()
        if message is None:
            return
        info = next((a for a in mime.attachments(message) if a["index"] == index), None)
        if info is None:
            return
        folder = Path.home() / "Downloads"
        try:
            out = subprocess.run(["xdg-user-dir", "DOWNLOAD"], capture_output=True, text=True, timeout=3).stdout.strip()
            if out:
                folder = Path(out)
        except (OSError, subprocess.TimeoutExpired):
            pass
        folder.mkdir(parents=True, exist_ok=True)
        name = re.sub(r"[/\\]", "_", info["name"])
        target, n = folder / name, 1
        while target.exists():
            target = folder / f"{Path(name).stem} ({n}){Path(name).suffix}"
            n += 1
        if mime.save_attachment(message, index, target):
            self.message.emit(self.textWith("saved_to", str(target)))

    # --- actions on messages ----------------------------------------------------------------------

    def _target(self, account_id="", folder="", uid=0):
        if account_id:
            return account_id, folder, int(uid)
        if self._selected:
            return self._selected
        return None

    @Slot(str, str, int)
    def toggleRead(self, account_id="", folder="", uid=0):
        target = self._target(account_id, folder, uid)
        if not target:
            return
        row = self.store.message(*target)
        if row:
            self.store.set_field(target[0], target[1], [target[2]], "seen", not row["seen"])
            self.refresh_list()
            self.engine.submit(target[0], "flag", folder=target[1], uids=[target[2]], flag="\\Seen", add=not row["seen"])

    @Slot(str, str, int)
    def toggleFlag(self, account_id="", folder="", uid=0):
        target = self._target(account_id, folder, uid)
        if not target:
            return
        row = self.store.message(*target)
        if row:
            self.store.set_field(target[0], target[1], [target[2]], "flagged", not row["flagged"])
            if self._selected == target:
                self._reading["flagged"] = not row["flagged"]
                self.readingChanged.emit()
            self.refresh_list()
            self.engine.submit(target[0], "flag", folder=target[1], uids=[target[2]], flag="\\Flagged",
                               add=not row["flagged"])

    @Slot(str, str, int)
    def togglePin(self, account_id="", folder="", uid=0):
        target = self._target(account_id, folder, uid)
        if not target:
            return
        row = self.store.message(*target)
        if row:
            self.store.set_field(target[0], target[1], [target[2]], "pinned", not row["pinned"])
            self.refresh_list()

    @Slot(str, str, int)
    def deleteMessage(self, account_id="", folder="", uid=0):
        target = self._target(account_id, folder, uid)
        if not target:
            return
        self.store.remove(*target[:2], [target[2]])
        if self._selected == target:
            self._clear_reading()
        self.refresh_list()
        self.engine.submit(target[0], "delete", folder=target[1], uids=[target[2]])

    def _move_to_role(self, target, role):
        destination = self.store.folder_by_role(target[0], role)
        if not destination:
            self.message.emit(self.text("no_folder_" + role))
            return
        self.moveMessage(destination, *target)

    @Slot(str, str, int)
    def archiveMessage(self, account_id="", folder="", uid=0):
        target = self._target(account_id, folder, uid)
        if target:
            self._move_to_role(target, "archive")

    @Slot(str, str, int)
    def junkMessage(self, account_id="", folder="", uid=0):
        target = self._target(account_id, folder, uid)
        if target:
            self._move_to_role(target, "junk")

    @Slot(str)
    @Slot(str, str, str, int)
    def moveMessage(self, destination, account_id="", folder="", uid=0):
        target = self._target(account_id, folder, uid)
        if not target or destination == target[1]:
            return
        self.store.remove(*target[:2], [target[2]])
        if self._selected == target:
            self._clear_reading()
        self.refresh_list()
        self.engine.submit(target[0], "move", folder=target[1], uids=[target[2]], target=destination)

    @Slot()
    def markAllRead(self):
        if not self._account:
            return
        unread = [m["uid"] for m in self.store.messages(self._account, self._folder) if not m["seen"]]
        if unread:
            self.store.set_field(self._account, self._folder, unread, "seen", True)
            self.refresh_list()
            self.engine.submit(self._account, "flag", folder=self._folder, uids=unread, flag="\\Seen", add=True)

    @Slot()
    def refresh(self):
        self.engine.sync_all()

    # --- writing ----------------------------------------------------------------------------------

    @Property("QVariantMap", notify=composeChanged)
    def compose(self):
        return self._compose

    def _account_for_compose(self):
        return self.account_store.get(self._account) or (self.account_store.accounts[0]
                                                           if self.account_store.accounts else None)

    def _signature_html(self, account):
        text = (account or {}).get("signature", "")
        if not text:
            return ""
        import html as _html
        return "<p><br></p><p>" + _html.escape(text).replace("\n", "<br>") + "</p>"

    @Slot()
    @Slot("QVariantMap")
    def newMail(self, fields=None):
        account = self._account_for_compose()
        if account is None:
            return
        fields = fields or {}
        import html as _html
        body = _html.escape(fields.get("body", "")).replace("\n", "<br>") if fields.get("body") else ""
        self._compose = {"mode": "new", "account": account["id"], "from": account["email"],
                         "to": fields.get("to", ""), "cc": fields.get("cc", ""), "bcc": fields.get("bcc", ""),
                         "subject": fields.get("subject", ""),
                         "body": "<p>" + body + "</p>" + self._signature_html(account),
                         "attachments": [], "sending": False, "replyTo": None, "showCc": bool(fields.get("cc"))}
        self._selected = None
        self._reading = {}
        self.readingChanged.emit()
        self.composeChanged.emit()
        self.composeStarted.emit()
        self.refresh_list()

    @Slot(str)
    def reply(self, mode):
        """mode: "reply", "replyAll" or "forward" for the open message."""
        message = self._current_message()
        if message is None or not self._selected:
            return
        account_id, folder, uid = self._selected
        account = self.account_store.get(account_id)
        own = account["email"].lower()
        sender = mime.addresses(message.get("Reply-To") or message.get("From"))
        to_list = [a for _n, a in sender]
        cc_list = []
        if mode == "replyAll":
            for _n, a in mime.addresses(message.get("To")) + mime.addresses(message.get("Cc")):
                if a.lower() != own and a not in to_list:
                    cc_list.append(a)
        subject = mime.decode(message.get("Subject"))
        if mode == "forward":
            subject = mime.prefixed(subject, self.text("prefix_forward"))
            to_list, cc_list = [], []
        else:
            subject = mime.prefixed(subject, self.text("prefix_reply"))
        header = [(self.text("header_from"), mime.decode(message.get("From"))),
                  (self.text("header_sent"), self.long_date(mime.message_date(message))),
                  (self.text("header_to"), mime.decode(message.get("To"))),
                  (self.text("header_subject"), mime.decode(message.get("Subject")))]
        attachments = []
        if mode == "forward":
            for info in mime.attachments(message):
                path = self.view_dir / "forward" / re.sub(r"[/\\]", "_", info["name"])
                path.parent.mkdir(parents=True, exist_ok=True)
                if mime.save_attachment(message, info["index"], path):
                    attachments.append({"path": str(path), "name": info["name"],
                                        "sizeText": self.size_text(info["size"])})
        self._compose = {"mode": mode, "account": account_id, "from": account["email"],
                         "to": ", ".join(to_list), "cc": ", ".join(cc_list), "bcc": "", "subject": subject,
                         "body": self._signature_html(account) + mime.quoted(message, header),
                         "attachments": attachments, "sending": False, "showCc": bool(cc_list),
                         "replyTo": {"folder": folder, "uid": uid,
                                     "messageId": (message.get("Message-ID") or "").strip(),
                                     "references": (message.get("References") or "").strip()}}
        self.composeChanged.emit()
        self.composeStarted.emit()

    @Slot(str, str)
    def setComposeField(self, field, value):
        if self._compose and field in ("to", "cc", "bcc", "subject", "body", "account"):
            self._compose[field] = value
            if field == "account":
                account = self.account_store.get(value)
                if account:
                    self._compose["from"] = account["email"]
                    self.composeChanged.emit()

    @Slot("QStringList")
    def attachFiles(self, urls):
        if not self._compose:
            return
        for url in urls:
            path = Path(QUrl(url).toLocalFile() if url.startswith("file:") else url)
            if path.is_file():
                self._compose["attachments"].append({"path": str(path), "name": path.name,
                                                     "sizeText": self.size_text(path.stat().st_size)})
        self.composeChanged.emit()

    @Slot(int)
    def removeAttachment(self, index):
        if self._compose and 0 <= index < len(self._compose["attachments"]):
            del self._compose["attachments"][index]
            self.composeChanged.emit()

    @Slot()
    def discard(self):
        self._compose = {}
        self.composeChanged.emit()

    @Slot(result=str)
    def send(self):
        """Sends the open draft; returns "" or the key of what is missing."""
        draft = self._compose
        if not draft:
            return "nothing"
        if not (draft["to"] or draft["cc"] or draft["bcc"]).strip():
            return "need_recipient"
        account = self.account_store.get(draft["account"])
        if account is None:
            return "nothing"
        reply = draft.get("replyTo") or {}
        message, recipients = mime.build(account["name"], account["email"], draft["to"], draft["cc"], draft["bcc"],
                                         draft["subject"], draft["body"],
                                         [a["path"] for a in draft["attachments"]],
                                         in_reply_to=reply.get("messageId", ""),
                                         references=reply.get("references", ""))
        if not recipients:
            return "need_recipient"
        draft["sending"] = True
        self.composeChanged.emit()
        self.engine.submit(account["id"], "send", request_id="compose", message_bytes=message.as_bytes(),
                           recipients=recipients,
                           reply_folder=reply.get("folder", "") if draft["mode"] != "forward" else "",
                           reply_uid=reply.get("uid", 0) if draft["mode"] != "forward" else 0)
        return ""

    @Slot(str, bool, str, str)
    def _on_sent(self, request_id, ok, kind, detail):
        if request_id != "compose" or not self._compose:
            return
        if ok:
            self._compose = {}
            self.composeChanged.emit()
            self.message.emit(self.text("sent_ok"))
        else:
            self._compose["sending"] = False
            self.composeChanged.emit()
            self.message.emit(self.text({"auth": "send_auth", "recipients": "send_recipients"}.get(kind, "send_failed")))

    @Slot(QObject, int, int, int, str)
    def applyFormat(self, quick_document, start, end, position, what):
        """Bold, italic, underline, bullets or numbering for the editor's
        selection (QQuickTextDocument from the TextArea)."""
        from PySide6.QtGui import QFont, QTextCharFormat, QTextCursor, QTextListFormat
        self._quick_document = quick_document          # keep the wrapper (AGENTS.md, Notepad)
        document = quick_document.textDocument()
        cursor = QTextCursor(document)
        cursor.setPosition(start if start != end else position)
        if start != end:
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        else:
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        if what in ("bullets", "numbering"):
            style = QTextListFormat.Style.ListDisc if what == "bullets" else QTextListFormat.Style.ListDecimal
            current = cursor.currentList()
            if current is not None and current.format().style() == style:
                block = cursor.blockFormat()
                current.remove(cursor.block())
                block.setIndent(0)
                cursor.setBlockFormat(block)
            else:
                cursor.createList(style)
            return
        char = cursor.charFormat()
        new = QTextCharFormat()
        if what == "bold":
            new.setFontWeight(QFont.Weight.Normal if char.fontWeight() >= QFont.Weight.Bold else QFont.Weight.Bold)
        elif what == "italic":
            new.setFontItalic(not char.fontItalic())
        elif what == "underline":
            new.setFontUnderline(not char.fontUnderline())
        cursor.mergeCharFormat(new)

    @Slot(str, result="QVariantList")
    def suggestions(self, text):
        text = text.strip().lower()
        if len(text) < 1:
            return []
        found = []
        for contact in self.store.contacts():
            if text in contact["address"].lower() or text in (contact["name"] or "").lower():
                found.append({"name": contact["name"] or contact["address"], "address": contact["address"],
                              "initials": mime.initials(contact["name"], contact["address"]),
                              "colour": mime.avatar_colour(contact["address"])})
            if len(found) >= 6:
                break
        return found

    @Property("QVariantList", notify=listChanged)
    def people(self):
        return [{"name": c["name"] or c["address"], "address": c["address"], "count": c["count"],
                 "initials": mime.initials(c["name"], c["address"]), "colour": mime.avatar_colour(c["address"])}
                for c in self.store.contacts()]

    # --- engine signals --------------------------------------------------------------------------

    @Slot(str, str, str)
    def _on_state(self, account_id, state, kind):
        self._states[account_id] = state if state != "error" else "error:" + kind
        self.statusChanged.emit()

    @Slot(str)
    def _on_folders(self, account_id):
        if not self._folder and account_id == self._account:
            self._folder = self.store.folder_by_role(account_id, "inbox") or "INBOX"
            self.refresh_list()
        self.changed.emit()

    @Slot(str, str)
    def _on_messages(self, account_id, folder):
        if self._query or (account_id == self._account and folder == self._folder):
            self.refresh_list()

    @Slot(str, str, str, str)
    def _on_new_mail(self, account_id, sender, subject, folder):
        notify(self.text("app_title"), f"{sender}\n{subject}")

    # --- other apps -----------------------------------------------------------------------------

    @Slot()
    def openCalendar(self):
        start(["veltos-calendar"])

    @Slot(str)
    def openUrl(self, url):
        if url.startswith(("http://", "https://", "mailto:")):
            if url.startswith("mailto:"):
                self.newMail(parse_mailto(url))
            else:
                start(["xdg-open", url])


def start(command):
    try:
        subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    except OSError:
        pass


def notify(title, body):
    start(["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications", "--object-path",
           "/org/freedesktop/Notifications", "--method", "org.freedesktop.Notifications.Notify", "VeltOS Mail",
           "0", "veltos-mail", title, body, "[]", "{'desktop-entry': <'veltos-mail'>}", "5000"])


def follow_frame(window):
    def update(*_args):
        margin = int(window.property("shadow") or 0)
        if margin:
            window.setMask(QRegion(margin, margin, max(1, window.width() - 2 * margin),
                                   max(1, window.height() - 2 * margin)))
        else:
            window.setMask(QRegion())
    for signal in (window.widthChanged, window.heightChanged, window.visibilityChanged):
        signal.connect(update)
    update()


def server_name():
    return f"veltos-mail-{os.getuid()}"


def hand_over(arguments):
    socket = QLocalSocket()
    socket.connectToServer(server_name())
    if not socket.waitForConnected(400):
        return False
    socket.write(json.dumps(arguments).encode("utf-8"))
    socket.flush()
    socket.waitForBytesWritten(1000)
    socket.disconnectFromServer()
    return True


def handle_arguments(backend, arguments):
    for argument in arguments:
        if argument.startswith("mailto:"):
            backend.newMail(parse_mailto(argument))


def main(argv=None):
    argv = sys.argv if argv is None else argv
    arguments = [a for a in argv[1:] if not a.startswith("--")]
    os.environ.setdefault("QML_DISABLE_DISK_CACHE", "1")
    from PySide6.QtWebEngineQuick import QtWebEngineQuick
    QtWebEngineQuick.initialize()
    app = QGuiApplication(argv)
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-mail")
    app.setDesktopFileName("veltos-mail")
    app.setWindowIcon(QIcon.fromTheme("veltos-mail"))
    if hand_over(arguments):
        return 0
    backend = Backend()
    app.setApplicationDisplayName(backend.text("app_title"))
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    follow_frame(window)
    server = QLocalServer(backend)
    QLocalServer.removeServer(server_name())
    if server.listen(server_name()):
        def connection():
            client = server.nextPendingConnection()

            def read():
                try:
                    handle_arguments(backend, json.loads(bytes(client.readAll()).decode("utf-8") or "[]"))
                except ValueError:
                    pass
                window.show()
                window.raise_()
                window.requestActivate()
            client.readyRead.connect(read)
        server.newConnection.connect(connection)
    handle_arguments(backend, arguments)
    QTimer.singleShot(300, backend.start)
    code = app.exec()
    shutil.rmtree(backend.view_dir, ignore_errors=True)
    sys.stdout.flush()
    os._exit(code)
