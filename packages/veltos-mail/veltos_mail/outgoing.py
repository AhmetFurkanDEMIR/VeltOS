"""Sending mail (SMTP, Python's smtplib) and signing in with OAuth 2.0.

OAuth 2.0 (Google, Microsoft): the user signs in in the web browser; VeltOS
Mail listens on 127.0.0.1 for the answer (RFC 8252, with PKCE) and keeps
the refresh token. Providers only accept registered programs, so this
needs VeltOS Mail's own client id from /etc/veltos/mail-oauth.json (or
~/.config/veltos-mail/oauth.json):

    {"microsoft": {"client_id": "..."}, "google": {"client_id": "...", "client_secret": "..."}}

Without one the provider's sign-in is not offered (accounts.py says what
works instead). Nothing here is a stand-in: an unconfigured provider is
reported as unavailable.
"""

import base64
import hashlib
import http.server
import json
import secrets
import smtplib
import socket
import ssl
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

from . import accounts
from .imapcore import MailError, xoauth2

TIMEOUT = 30
ENDPOINTS = {
    "google": {"auth": "https://accounts.google.com/o/oauth2/v2/auth",
               "token": "https://oauth2.googleapis.com/token",
               "scope": "https://mail.google.com/"},
    "microsoft": {"auth": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                  "token": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                  "scope": "https://outlook.office.com/IMAP.AccessAsUser.All "
                           "https://outlook.office.com/SMTP.Send offline_access"},
}


# --- SMTP ---------------------------------------------------------------------------------------

def send(account, secret, message, recipients, factory=None):
    """Sends an EmailMessage to `recipients` through the account's server."""
    context = ssl.create_default_context()
    host, port = account["smtpHost"], int(account["smtpPort"])
    try:
        if factory is not None:
            server = factory(account)
        elif account.get("smtpSecurity") == "ssl":
            server = smtplib.SMTP_SSL(host, port, context=context, timeout=TIMEOUT)
        else:
            server = smtplib.SMTP(host, port, timeout=TIMEOUT)
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
    except (OSError, socket.timeout, smtplib.SMTPException) as error:
        raise MailError("connect", str(error)) from error
    try:
        if account.get("auth") == "oauth2":
            token = base64.b64encode(xoauth2(account["username"], secret)).decode("ascii")
            code, answer = server.docmd("AUTH", "XOAUTH2 " + token)
            if code != 235:
                raise MailError("auth", answer.decode("utf-8", "replace") if isinstance(answer, bytes) else str(answer))
        else:
            server.login(account["username"], secret)
        server.send_message(message, from_addr=account["email"], to_addrs=recipients)
    except smtplib.SMTPAuthenticationError as error:
        raise MailError("auth", str(error)) from error
    except smtplib.SMTPRecipientsRefused as error:
        raise MailError("recipients", ", ".join(error.recipients)) from error
    except (OSError, smtplib.SMTPException) as error:
        raise MailError("server", str(error)) from error
    finally:
        try:
            server.quit()
        except Exception:
            pass


# --- OAuth 2.0 ----------------------------------------------------------------------------------

def oauth_config(paths=None):
    paths = paths or [Path("/etc/veltos/mail-oauth.json"), accounts.config_home() / "veltos-mail/oauth.json"]
    config = {}
    for path in paths:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for provider, values in data.items():
            if isinstance(values, dict) and values.get("client_id"):
                config[provider] = values
    return config


def oauth_available(provider, config=None):
    return provider in ENDPOINTS and provider in (config if config is not None else oauth_config())


class _Answer(http.server.BaseHTTPRequestHandler):
    result = None

    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        type(self).result = {k: v[0] for k, v in query.items()}
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("<html><body style='font-family:sans-serif;text-align:center;padding-top:15vh'>"
                         "<h2>VeltOS Mail</h2><p>You can close this tab and go back to VeltOS Mail.</p>"
                         "</body></html>".encode("utf-8"))

    def log_message(self, *_args):
        pass


def authorize(provider, email, open_url, config=None, wait=300):
    """The browser sign-in; returns {"access_token", "refresh_token", "expires"}."""
    config = config if config is not None else oauth_config()
    if not oauth_available(provider, config):
        raise MailError("oauth_unavailable", provider)
    client = config[provider]
    endpoint = ENDPOINTS[provider]
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode("ascii").rstrip("=")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode("ascii").rstrip("=")
    state = secrets.token_urlsafe(16)

    class Handler(_Answer):
        result = None
    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect = f"http://127.0.0.1:{server.server_port}/"
    params = {"client_id": client["client_id"], "response_type": "code", "redirect_uri": redirect,
              "scope": endpoint["scope"], "state": state, "code_challenge": challenge,
              "code_challenge_method": "S256", "login_hint": email}
    if provider == "google":
        params.update({"access_type": "offline", "prompt": "consent"})
    open_url(endpoint["auth"] + "?" + urllib.parse.urlencode(params))
    server.timeout = 1
    deadline = time.time() + wait
    try:
        while Handler.result is None and time.time() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    answer = Handler.result or {}
    if answer.get("state") != state or "code" not in answer:
        raise MailError("auth", answer.get("error_description") or answer.get("error") or "no answer")
    tokens = _token_request(endpoint["token"], {
        "client_id": client["client_id"], "grant_type": "authorization_code", "code": answer["code"],
        "redirect_uri": redirect, "code_verifier": verifier,
        **({"client_secret": client["client_secret"]} if client.get("client_secret") else {})})
    return tokens


def refresh(provider, refresh_token, config=None):
    config = config if config is not None else oauth_config()
    if not oauth_available(provider, config):
        raise MailError("oauth_unavailable", provider)
    client = config[provider]
    tokens = _token_request(ENDPOINTS[provider]["token"], {
        "client_id": client["client_id"], "grant_type": "refresh_token", "refresh_token": refresh_token,
        **({"client_secret": client["client_secret"]} if client.get("client_secret") else {})})
    tokens.setdefault("refresh_token", refresh_token)
    return tokens


def _token_request(url, fields):
    data = urllib.parse.urlencode(fields).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=TIMEOUT) as response:
            answer = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as error:
        raise MailError("auth", str(error)) from error
    if "access_token" not in answer:
        raise MailError("auth", answer.get("error_description") or answer.get("error") or "no token")
    answer["expires"] = int(time.time()) + int(answer.get("expires_in", 3600)) - 60
    return answer


def run_in_thread(function, *args):
    thread = threading.Thread(target=function, args=args, daemon=True)
    thread.start()
    return thread
