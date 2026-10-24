"""Mail accounts of VeltOS Mail: where they are kept, the servers of the
common providers, and the passwords.

An account is a plain dict (kept in ~/.config/veltos-mail/accounts.json):
id, name (the person's name), email, the IMAP server (incoming) and the
SMTP server (outgoing) with their ports and security ("ssl", "starttls"),
the user name and the sign-in kind ("password" or "oauth2"). Passwords and
OAuth tokens are not in that file: they go to the Secret Service (KWallet
on Plasma) when it answers without asking, otherwise to a file only the
user can read (~/.local/share/veltos-mail/secrets.json, mode 0600), as
mail programs without a keyring do.

Providers: the settings of the big providers are known (`PROVIDERS`), so
adding an account needs only the address and the password. Gmail, Yahoo,
iCloud, Yandex and AOL take an app password (the account's own password is
refused by their IMAP servers). Outlook.com, Hotmail and Microsoft 365 take
only Microsoft's sign-in (OAuth 2.0) since September 2024; it needs VeltOS
Mail's own registration with Microsoft (`oauth.py`), so without one those
accounts cannot be added and the user is told so. Other domains: the usual
host names (imap.DOMAIN, mail.DOMAIN, smtp.DOMAIN) are tried.
"""

import json
import os
import re
import secrets as _random
import stat
from pathlib import Path

# domain(s) -> provider settings
PROVIDERS = {
    "gmail": {
        "domains": ("gmail.com", "googlemail.com"),
        "title": "Gmail", "imap": ("imap.gmail.com", 993, "ssl"), "smtp": ("smtp.gmail.com", 465, "ssl"),
        "auth": "app_password", "oauth": "google",
        "help": "https://myaccount.google.com/apppasswords",
        # Gmail keeps a copy of sent mail itself: no APPEND to Sent.
        "saves_sent": True,
    },
    "microsoft": {
        "domains": ("outlook.com", "hotmail.com", "live.com", "msn.com", "outlook.com.tr", "hotmail.com.tr",
                    "hotmail.co.uk", "hotmail.fr", "hotmail.de", "live.co.uk", "outlook.de", "outlook.fr"),
        "title": "Outlook.com", "imap": ("outlook.office365.com", 993, "ssl"),
        "smtp": ("smtp-mail.outlook.com", 587, "starttls"), "auth": "oauth_only", "oauth": "microsoft",
        "help": "https://outlook.live.com/mail/",
        "saves_sent": True,
    },
    "yahoo": {
        "domains": ("yahoo.com", "ymail.com", "rocketmail.com", "yahoo.co.uk", "yahoo.de", "yahoo.fr"),
        "title": "Yahoo", "imap": ("imap.mail.yahoo.com", 993, "ssl"), "smtp": ("smtp.mail.yahoo.com", 465, "ssl"),
        "auth": "app_password", "help": "https://login.yahoo.com/account/security",
    },
    "icloud": {
        "domains": ("icloud.com", "me.com", "mac.com"),
        "title": "iCloud", "imap": ("imap.mail.me.com", 993, "ssl"), "smtp": ("smtp.mail.me.com", 587, "starttls"),
        "auth": "app_password", "help": "https://account.apple.com/account/manage",
    },
    "yandex": {
        "domains": ("yandex.com", "yandex.ru", "yandex.com.tr", "ya.ru", "yandex.ua", "yandex.by", "yandex.kz"),
        "title": "Yandex", "imap": ("imap.yandex.com", 993, "ssl"), "smtp": ("smtp.yandex.com", 465, "ssl"),
        "auth": "app_password", "help": "https://id.yandex.com/security/app-passwords",
    },
    "aol": {
        "domains": ("aol.com",),
        "title": "AOL", "imap": ("imap.aol.com", 993, "ssl"), "smtp": ("smtp.aol.com", 465, "ssl"),
        "auth": "app_password", "help": "https://login.aol.com/account/security",
    },
    "gmx": {
        "domains": ("gmx.com", "gmx.net", "gmx.de", "gmx.at", "gmx.ch", "web.de"),
        "title": "GMX", "imap": ("imap.{domain}", 993, "ssl"), "smtp": ("mail.{domain}", 587, "starttls"),
        "auth": "password",
    },
    "zoho": {
        "domains": ("zoho.com", "zohomail.com"),
        "title": "Zoho Mail", "imap": ("imap.zoho.com", 993, "ssl"), "smtp": ("smtp.zoho.com", 465, "ssl"),
        "auth": "password",
    },
    "mailru": {
        "domains": ("mail.ru", "inbox.ru", "list.ru", "bk.ru"),
        "title": "Mail.ru", "imap": ("imap.mail.ru", 993, "ssl"), "smtp": ("smtp.mail.ru", 465, "ssl"),
        "auth": "app_password", "help": "https://account.mail.ru/user/2-step-auth/passwords",
    },
    "fastmail": {
        "domains": ("fastmail.com", "fastmail.fm"),
        "title": "Fastmail", "imap": ("imap.fastmail.com", 993, "ssl"), "smtp": ("smtp.fastmail.com", 465, "ssl"),
        "auth": "app_password", "help": "https://app.fastmail.com/settings/security/apps",
    },
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SECURITIES = ("ssl", "starttls")


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def data_home():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")


def cache_home():
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")


def valid_email(text):
    return bool(EMAIL_RE.match((text or "").strip()))


def domain_of(email):
    return email.strip().rsplit("@", 1)[-1].lower()


def provider_for(email):
    """(key, settings) of the provider an address belongs to, or (None, None)."""
    domain = domain_of(email)
    for key, provider in PROVIDERS.items():
        if domain in provider["domains"]:
            return key, provider
    return None, None


def _host(template, domain):
    return template.replace("{domain}", domain)


def guess_settings(email):
    """Candidate server settings for an address: the provider's, else the
    usual host names of its domain (tried in order by the caller)."""
    domain = domain_of(email)
    key, provider = provider_for(email)
    if provider:
        imap, smtp = provider["imap"], provider["smtp"]
        return [{"provider": key, "imapHost": _host(imap[0], domain), "imapPort": imap[1], "imapSecurity": imap[2],
                 "smtpHost": _host(smtp[0], domain), "smtpPort": smtp[1], "smtpSecurity": smtp[2]}]
    candidates = []
    for imap_host in (f"imap.{domain}", f"mail.{domain}", domain):
        for smtp_host in (f"smtp.{domain}", f"mail.{domain}", domain):
            candidates.append({"provider": "", "imapHost": imap_host, "imapPort": 993, "imapSecurity": "ssl",
                               "smtpHost": smtp_host, "smtpPort": 465, "smtpSecurity": "ssl"})
            candidates.append({"provider": "", "imapHost": imap_host, "imapPort": 993, "imapSecurity": "ssl",
                               "smtpHost": smtp_host, "smtpPort": 587, "smtpSecurity": "starttls"})
    # Keep the order, drop repeats (mail.DOMAIN appears twice for some).
    seen, unique = set(), []
    for c in candidates:
        key = (c["imapHost"], c["smtpHost"], c["smtpPort"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def discovery(email):
    """(imap, smtp) candidates for an address, each a list of
    (host, port, security) without repeats, in the order to try."""
    imap, smtp = [], []
    for c in guess_settings(email):
        for target, item in ((imap, (c["imapHost"], c["imapPort"], c["imapSecurity"])),
                             (smtp, (c["smtpHost"], c["smtpPort"], c["smtpSecurity"]))):
            if item not in target:
                target.append(item)
    return imap, smtp


def new_account(email, name, settings, auth="password", username=""):
    return {
        "id": _random.token_hex(6), "email": email.strip(), "name": name.strip() or email.split("@")[0],
        "username": username.strip() or email.strip(), "auth": auth,
        "imapHost": settings["imapHost"], "imapPort": int(settings["imapPort"]),
        "imapSecurity": settings["imapSecurity"], "smtpHost": settings["smtpHost"],
        "smtpPort": int(settings["smtpPort"]), "smtpSecurity": settings["smtpSecurity"],
        "provider": settings.get("provider", ""), "signature": "",
    }


def saves_sent_itself(account):
    provider = PROVIDERS.get(account.get("provider", ""), {})
    return bool(provider.get("saves_sent"))


class AccountStore:
    """accounts.json: the accounts in the order they were added."""

    def __init__(self, path=None):
        self.path = Path(path or config_home() / "veltos-mail/accounts.json")
        self.accounts = []
        self.settings = {}
        self.load()

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        self.accounts = [a for a in data.get("accounts", []) if isinstance(a, dict) and a.get("email")]
        self.settings = data.get("settings", {}) if isinstance(data.get("settings"), dict) else {}

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"accounts": self.accounts, "settings": self.settings}, indent=1,
                                  ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def get(self, account_id):
        return next((a for a in self.accounts if a["id"] == account_id), None)

    def add(self, account):
        self.accounts = [a for a in self.accounts if a["email"].lower() != account["email"].lower()]
        self.accounts.append(account)
        self.save()

    def remove(self, account_id):
        self.accounts = [a for a in self.accounts if a["id"] != account_id]
        self.save()

    def update(self, account_id, **values):
        account = self.get(account_id)
        if account:
            account.update(values)
            self.save()

    def setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value
        self.save()


class SecretStore:
    """Passwords and tokens by account id. The Secret Service when it is
    there and unlocked (it must not ask the user anything), else a 0600
    file."""

    ATTRIBUTE = "veltos-mail-account"

    def __init__(self, path=None, use_service=True):
        self.path = Path(path or data_home() / "veltos-mail/secrets.json")
        self._service = self._open_service() if use_service else None

    def _open_service(self):
        try:
            import secretstorage
            connection = secretstorage.dbus_init()
            collection = secretstorage.get_default_collection(connection)
            if collection.is_locked():
                return None
            return collection
        except Exception:          # no service, no D-Bus, locked, not installed
            return None

    @property
    def backend(self):
        return "service" if self._service is not None else "file"

    def _read_file(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _write_file(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
        tmp.replace(self.path)

    def get(self, account_id):
        if self._service is not None:
            try:
                for item in self._service.search_items({self.ATTRIBUTE: account_id}):
                    return item.get_secret().decode("utf-8")
            except Exception:
                pass
        return self._read_file().get(account_id, "")

    def set(self, account_id, secret):
        if self._service is not None:
            try:
                self._service.create_item(f"VeltOS Mail ({account_id})", {self.ATTRIBUTE: account_id},
                                          secret.encode("utf-8"), replace=True)
                return
            except Exception:
                pass
        data = self._read_file()
        data[account_id] = secret
        self._write_file(data)

    def delete(self, account_id):
        if self._service is not None:
            try:
                for item in self._service.search_items({self.ATTRIBUTE: account_id}):
                    item.delete()
            except Exception:
                pass
        data = self._read_file()
        if account_id in data:
            del data[account_id]
            self._write_file(data)
