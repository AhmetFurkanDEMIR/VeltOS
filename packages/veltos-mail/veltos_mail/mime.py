"""Messages for VeltOS Mail: reading them (headers, preview, the body to
show) and writing them (new mail, reply, forward), on Python's email
package.

Showing a mail: the HTML part (or the text part turned into HTML) is
cleaned before the reading pane gets it: scripts, frames, forms, event
handlers and `javascript:` links are removed (the reading pane also runs
with JavaScript off), and pictures from the internet are replaced by
nothing until the user chooses "Show pictures" (they can tell the sender
that and when a mail was read). Pictures inside the mail (cid:) are
written next to the page and shown.
"""

import datetime
import email
import email.policy
import email.utils
import hashlib
import html
import mimetypes
import re
from email.header import Header, decode_header, make_header
from email.message import EmailMessage
from pathlib import Path

PREVIEW_CHARS = 180
# Pictures left out: a transparent pixel instead of a broken picture.
BLANK_PICTURE = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
AVATAR_COLOURS = ("#0F6CBD", "#C239B3", "#E3008C", "#CA5010", "#498205", "#038387", "#8764B8", "#4F6BED",
                  "#986F0B", "#C50F1F", "#00727C", "#7A7574")
BLOCKED_TAGS = ("script", "iframe", "frame", "frameset", "object", "embed", "applet", "form", "base", "meta",
                "link")
REMOTE_RE = re.compile(r"""(?P<attr>\b(?:src|background|poster|srcset)\s*=\s*)(?P<q>["']?)(?P<url>(?:https?:)?//[^"'\s>]+)(?P=q)""",
                       re.IGNORECASE)
CSS_URL_RE = re.compile(r"""url\(\s*(['"]?)(?:https?:)?//[^)]*\1\s*\)""", re.IGNORECASE)
CID_RE = re.compile(r"""\bcid:([^"'\s>)]+)""", re.IGNORECASE)


def raw_8bit(text):
    """Header text with raw 8-bit bytes (sent without RFC 2047 words, as
    many programs do): Python's parser keeps them as surrogate escapes;
    they are UTF-8, or else Turkish Windows-1254."""
    if not any("\udc80" <= ch <= "\udcff" for ch in text):
        return text
    raw = text.encode("ascii", "surrogateescape")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1254", "replace")


def _header_text(header):
    """A Header object (what the compat32 parser gives for a header with
    raw 8-bit bytes: charset "unknown-8bit") as text."""
    parts = []
    for chunk, charset in decode_header(header):
        if isinstance(chunk, bytes):
            if charset in (None, "unknown-8bit"):
                try:
                    chunk = chunk.decode("utf-8")
                except UnicodeDecodeError:
                    chunk = chunk.decode("cp1254", "replace")
            else:
                try:
                    chunk = chunk.decode(charset, "replace")
                except LookupError:
                    chunk = chunk.decode("utf-8", "replace")
        parts.append(chunk)
    return "".join(parts)


def decode(value):
    """A header value as text (RFC 2047 encoded words decoded)."""
    if value is None:
        return ""
    if isinstance(value, Header):
        value = _header_text(value)
    text = raw_8bit(str(value))
    try:
        return str(make_header(decode_header(text))).strip()
    except (UnicodeDecodeError, UnicodeEncodeError, LookupError, ValueError):
        return text.strip()


def parse_bytes(raw):
    return email.message_from_bytes(raw, policy=email.policy.compat32)


def addresses(value):
    """[(name, address)] of an address header."""
    return [(decode(name), addr) for name, addr in email.utils.getaddresses([decode(value)]) if addr or name]


def display_name(name, addr):
    return name or (addr.split("@")[0] if addr else "")


def message_date(message, fallback=None):
    """Epoch seconds of the Date header (or the server's arrival time)."""
    value = message.get("Date")
    try:
        parsed = email.utils.parsedate_to_datetime(value) if value else None
    except (TypeError, ValueError, IndexError):
        parsed = None
    if parsed is None and fallback:
        try:
            parsed = email.utils.parsedate_to_datetime(fallback)
        except (TypeError, ValueError, IndexError):
            parsed = None
    if parsed is None:
        return 0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return int(parsed.timestamp())


def _text_of(part):
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, "replace")
    except LookupError:
        return payload.decode("utf-8", "replace")


def html_to_text(markup):
    markup = re.sub(r"(?is)<(script|style|head|title)[^>]*>.*?</\1>", " ", markup)
    markup = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>|</li>|</table>", "\n", markup)
    markup = re.sub(r"(?i)</t[dh]>", " ", markup)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", "", markup))
    return "\n".join(re.sub(r"[ \t\xa0]+", " ", line).strip() for line in text.splitlines())


def bodies(message):
    """(text, html) of a message; either may be ""."""
    text, markup = "", ""
    for part in message.walk() if message.is_multipart() else [message]:
        if part.is_multipart():
            continue
        disposition = (part.get("Content-Disposition") or "").lower()
        if disposition.startswith("attachment"):
            continue
        kind = part.get_content_type()
        if kind == "text/plain" and not text:
            text = _text_of(part)
        elif kind == "text/html" and not markup:
            markup = _text_of(part)
    return text, markup


def preview(message):
    text, markup = bodies(message)
    source = text if text.strip() else html_to_text(markup)
    lines = [line.strip() for line in source.splitlines()]
    # Quoted replies and signatures add nothing to a preview.
    lines = [line for line in lines if line and not line.startswith(">")]
    return re.sub(r"\s+", " ", " ".join(lines)).strip()[:PREVIEW_CHARS]


def attachments(message):
    """[{"name", "type", "size", "index"}] of the parts that are files."""
    found = []
    for index, part in enumerate(message.walk()):
        if part.is_multipart():
            continue
        disposition = (part.get("Content-Disposition") or "").lower()
        name = decode(part.get_filename() or "")
        if disposition.startswith("attachment") or (name and not disposition.startswith("inline")
                                                    and part.get_content_maintype() != "text"):
            payload = part.get_payload(decode=True) or b""
            found.append({"name": name or f"attachment-{index}", "type": part.get_content_type(),
                          "size": len(payload), "index": index})
    return found


def has_attachments(message):
    content_type = (message.get("Content-Type") or "").lower()
    if "multipart/mixed" in content_type:
        return True
    return bool(attachments(message)) if message.is_multipart() else False


def is_other(message, own=""):
    """Outlook's "Other" tab: newsletters, notifications and bulk mail
    (a List-Unsubscribe or List-Id header, bulk precedence, no-reply
    senders). Everything else is "Focused"."""
    if message.get("List-Unsubscribe") or message.get("List-Id"):
        return True
    if (message.get("Precedence") or "").lower() in ("bulk", "list", "junk"):
        return True
    sender = " ".join(addr for _name, addr in addresses(message.get("From"))).lower()
    return bool(re.search(r"\b(no-?reply|do-?not-?reply|notifications?|newsletter|mailer-daemon)@", sender))


def summary(raw, internaldate=""):
    """What the message list needs, from the first part of a message."""
    message = parse_bytes(raw)
    sender = addresses(message.get("From"))
    name, addr = sender[0] if sender else ("", "")
    return {
        "fromName": display_name(name, addr), "fromAddr": addr,
        "to": ", ".join(display_name(n, a) for n, a in addresses(message.get("To"))),
        "subject": decode(message.get("Subject")),
        "date": message_date(message, internaldate),
        "messageId": (message.get("Message-ID") or "").strip(),
        "preview": preview(message), "attachments": has_attachments(message),
        "other": is_other(message),
    }


def initials(name, addr=""):
    words = [w for w in re.split(r"[\s._-]+", name or "") if w and w[0].isalnum()]
    if len(words) >= 2:
        return (words[0][0] + words[-1][0]).upper()
    if words:
        return words[0][:2].upper()
    return (addr[:1] or "?").upper()


def avatar_colour(addr):
    digest = hashlib.sha1((addr or "").lower().encode("utf-8")).digest()
    return AVATAR_COLOURS[digest[0] % len(AVATAR_COLOURS)]


# --- showing a message ------------------------------------------------------------------------------

def text_to_html(text):
    escaped = html.escape(text)
    escaped = re.sub(r"(https?://[^\s<>&\"']+)", r'<a href="\1">\1</a>', escaped)
    lines = []
    for line in escaped.split("\n"):
        if line.startswith("&gt;"):
            lines.append(f'<span class="quote">{line}</span>')
        else:
            lines.append(line)
    return '<div class="plain">' + "<br>".join(lines) + "</div>"


def clean_html(markup, allow_remote=False):
    """(markup, blocked) with active content removed and, unless allowed,
    pictures from the internet left out; blocked = remote pictures found."""
    for tag in BLOCKED_TAGS:
        markup = re.sub(rf"(?is)<{tag}\b[^>]*>.*?</{tag}\s*>", "", markup)
        markup = re.sub(rf"(?is)<{tag}\b[^>]*/?>", "", markup)
    markup = re.sub(r"""(?is)\son\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""", "", markup)
    markup = re.sub(r"""(?is)(href|src)\s*=\s*(["']?)\s*javascript:[^"'>\s]*\2""", r'\1="#"', markup)
    blocked = bool(REMOTE_RE.search(markup) or CSS_URL_RE.search(markup))
    if not allow_remote:
        markup = REMOTE_RE.sub(lambda m: m.group("attr") + '"' + BLANK_PICTURE + '"', markup)
        markup = CSS_URL_RE.sub("none", markup)
    return markup, blocked


PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' file:; font-src file: data:{img}">
<style>
:root {{ color-scheme: {scheme}; }}
html, body {{ margin: 0; padding: 0; background: {background}; color: {text}; }}
body {{ font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif; font-size: 14.5px; line-height: 1.45;
        padding: 4px 20px 24px 20px; word-wrap: break-word; overflow-wrap: anywhere; }}
a {{ color: {link}; }}
img {{ max-width: 100%; height: auto; }}
.plain {{ white-space: normal; }}
.quote {{ color: {quote}; }}
blockquote {{ border-left: 3px solid {line}; margin: 0 0 0 4px; padding-left: 12px; color: {quote}; }}
table {{ max-width: 100% !important; }}
</style></head><body>{body}</body></html>"""


def page(message, dark=False, allow_remote=False):
    """(html page, blocked) for the reading pane."""
    text, markup = bodies(message)
    if markup.strip():
        body_markup, blocked = clean_html(_body_inner(markup), allow_remote)
    else:
        body_markup, blocked = text_to_html(text), False
    colours = {"scheme": "dark light" if dark else "light", "background": "#292929" if dark else "#FFFFFF",
               "text": "#FFFFFF" if dark else "#242424", "link": "#479EF5" if dark else "#0F6CBD",
               "quote": "#ADADAD" if dark else "#616161", "line": "#525252" if dark else "#D1D1D1"}
    img = "; img-src file: data: about:" + (" http: https:" if allow_remote else "")
    return PAGE.format(body=body_markup, img=img, **colours), blocked


def _body_inner(markup):
    match = re.search(r"(?is)<body[^>]*>(.*)</body>", markup)
    styles = "".join(re.findall(r"(?is)<style[^>]*>.*?</style>", markup))
    return styles + (match.group(1) if match else markup)


def inline_parts(message):
    """{content-id: (filename, bytes)} of the pictures the HTML refers to."""
    found = {}
    for part in message.walk():
        cid = (part.get("Content-ID") or "").strip().strip("<>")
        if cid and not part.is_multipart():
            payload = part.get_payload(decode=True) or b""
            extension = mimetypes.guess_extension(part.get_content_type()) or ".bin"
            safe = re.sub(r"[^A-Za-z0-9._-]", "_", cid)[:80]
            found[cid] = (safe + extension, payload)
    return found


def write_view(message, folder, dark=False, allow_remote=False):
    """Writes the page and its inline pictures into `folder`; returns
    (path of index.html, blocked)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    markup, blocked = page(message, dark, allow_remote)
    parts = inline_parts(message)
    for cid, (filename, payload) in parts.items():
        (folder / filename).write_bytes(payload)
    markup = CID_RE.sub(lambda m: parts[m.group(1)][0] if m.group(1) in parts else "about:blank", markup)
    index = folder / "index.html"
    index.write_text(markup, encoding="utf-8")
    return index, blocked


def save_attachment(message, index, target):
    for i, part in enumerate(message.walk()):
        if i == index:
            Path(target).write_bytes(part.get_payload(decode=True) or b"")
            return True
    return False


# --- writing ----------------------------------------------------------------------------------

def html_to_plain(markup):
    return re.sub(r"\n{3,}", "\n\n", html_to_text(markup)).strip()


def build(sender_name, sender_addr, to, cc, bcc, subject, body_html, attachments_paths=(),
          in_reply_to="", references=""):
    """An EmailMessage: text and HTML alternatives and the attached files."""
    message = EmailMessage()
    message["From"] = email.utils.formataddr((sender_name, sender_addr))
    if to:
        message["To"] = to
    if cc:
        message["Cc"] = cc
    message["Subject"] = subject
    message["Date"] = email.utils.formatdate(localtime=True)
    message["Message-ID"] = email.utils.make_msgid(domain=sender_addr.rsplit("@", 1)[-1] or None)
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
        message["References"] = (references + " " + in_reply_to).strip()
    message["X-Mailer"] = "VeltOS Mail"
    message.set_content(html_to_plain(body_html) + "\n")
    message.add_alternative(body_html, subtype="html")
    for path in attachments_paths:
        path = Path(path)
        kind, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (kind or "application/octet-stream").split("/", 1)
        message.add_attachment(path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name)
    # Empty fields must not reach getaddresses: Python 3.13's strict parser
    # takes "a@b.c, , " as malformed and returns no address at all.
    fields = [value for value in (to, cc, bcc) if value and value.strip(" ,;")]
    recipients = [addr for _n, addr in email.utils.getaddresses(fields) if addr]
    return message, recipients


def prefixed(subject, prefix):
    if re.match(rf"(?i)^{re.escape(prefix)}\s", subject or ""):
        return subject
    return f"{prefix} {subject}".strip()


def quoted(message, header_lines):
    """The original message under a line, as Outlook quotes it."""
    text, markup = bodies(message)
    original = _body_inner(clean_html(markup, allow_remote=False)[0]) if markup.strip() else text_to_html(text)
    head = "<br>".join(f"<b>{html.escape(k)}</b> {html.escape(v)}" for k, v in header_lines)
    # A table cell's top border: Qt's editor draws <hr> as a thick black bar.
    return ('<p><br></p><table width="100%" cellspacing="0" cellpadding="0"><tr>'
            '<td style="border-top: 1px solid #E1E1E1; font-size: 1px;">&nbsp;</td></tr></table>'
            f'<div style="font-size:13px">{head}</div><br>{original}')
