# veltos-mail

VeltOS Mail: e-mail in the layout of Windows 11's new Outlook (PySide6 +
QML). It replaces the Thunderbird-based VeltOS Mail of 2026-10-21/22, which
could only be restyled from the outside (product owner, 2026-10-23: "write
VeltOS Mail again, exactly Outlook: icon, sign-in screen, everything").

## The window (`veltos_mail/qml/`)

- **Header** (`Header.qml`): Outlook's brand blue band (`#0F6CBD`; dark
  grey in dark mode) with the app's icon and name, the search box in the
  middle of the window (searches all accounts as you type), Settings and
  the window buttons. The window draws its own frame and shadow.
- **App bar** (`AppRail.qml`): Mail, Calendar (opens VeltOS Calendar) and
  People.
- **Ribbon** (`Ribbon.qml`): the Home / View / Help tabs with the
  simplified ribbon: New mail (blue), Delete, Archive, Report, Move to,
  Reply, Reply all, Forward, Read / Unread, Flag, Pin, more; View: folder
  pane, Focused Inbox, message preview, sender images, Sync; Help: About,
  keyboard shortcuts. While writing, the Message tab: Attach file, Bold,
  Italic, Underline, Bullets, Numbering, Discard.
- **Folder pane** (`FolderPane.qml`): Favorites (Inbox, Sent Items,
  Drafts of every account), then each account (collapsible) with its
  folders in Outlook's names and order, unread counts, "Add account".
- **Message list** (`MessageList.qml`): the folder's name, Focused / Other
  (newsletters and notifications go to Other: List-Unsubscribe / List-Id,
  bulk precedence, no-reply senders), groups Pinned / Today / Yesterday /
  This week / Last week / This month / Last month / Older; sender picture
  (initials on a colour), name, subject, preview, time; unread messages
  with the blue bar, bold name and blue subject; Delete / Read / Flag /
  Pin on hover; the actions menu on right-click; arrow keys and Delete.
- **Reading pane** (`ReadingPane.qml`): subject, sender card with
  Reply / Reply all / Forward / More and the date, "pictures were not
  downloaded" bar with Show pictures, attachments (open, save to
  Downloads), the message in Qt WebEngine. New mail, reply and forward open
  in the same place (`ComposePane.qml`): Send / Discard, From (several
  accounts), To with Cc / Bcc and completion from people you got mail
  from, Add a subject, attachments, rich text.
- **Add your account** (`AddAccount.qml`): the first start and "Add
  account": the address; then the password, or an app password with the
  link to make one (Gmail, Yahoo, iCloud, Yandex, AOL, Mail.ru,
  Fastmail), the person's name and Advanced settings (IMAP and SMTP
  servers); "You're all set!".
- **Settings** (`SettingsDialog.qml`): Accounts (remove, add, signature),
  General, Mail (Focused Inbox, preview, sender images).
- **People** (`PeoplePage.qml`): everyone you got mail from, with Send email.
- Outlook's shortcuts: Ctrl+N, Ctrl+R, Ctrl+Shift+R, Ctrl+F (forward),
  Ctrl+Q / Ctrl+U, Insert (flag), Delete, Ctrl+E (search), Ctrl+Enter
  (send), F5. English and Turkish (Outlook's Turkish folder names: Gelen
  Kutusu, Gönderilmiş Öğeler, Silinmiş Öğeler, Gereksiz E-posta; "YNT:",
  "İLT:").

## Mail

- `accounts.py`: accounts in `~/.config/veltos-mail/accounts.json`;
  passwords in the Secret Service when it answers without asking, else in
  `~/.local/share/veltos-mail/secrets.json` (mode 0600); the servers of the
  common providers, else the usual host names of the domain.
- `imapcore.py` (imaplib): SSL/TLS or STARTTLS, LOGIN or XOAUTH2, folders
  with RFC 6154 special-use roles (or the usual names, English and
  Turkish), modified UTF-7 names, FETCH parsing, MOVE (or COPY + delete),
  APPEND.
- `sync.py`: one thread per account; the newest 300 Inbox and 100 other
  messages the first time (headers and the first 12 KB for the preview),
  then new messages, flags and deletions of the newest 500; whole messages
  when opened (`~/.cache/veltos-mail/bodies/`); a new-mail notification;
  every 90 s.
- `store.py`: the local copy in SQLite (`~/.cache/veltos-mail/mail.sqlite`).
- `mime.py` (Python's email): summaries and previews, the page for the
  reading pane (scripts, frames, forms, event handlers and `javascript:`
  links removed, a Content-Security-Policy without scripts, pictures from
  the internet left out until allowed, inline `cid:` pictures written next
  to the page), new messages with text and HTML parts and attachments,
  replies and forwards (Outlook's header block).
- `outgoing.py`: SMTP (smtplib), and OAuth 2.0 with PKCE and a loopback
  redirect for Google and Microsoft. **Outlook.com, Hotmail and Live
  accounts accept only Microsoft's sign-in** (basic authentication ended
  on 2024-09-16), and Microsoft and Google accept only registered
  programs: OAuth works once VeltOS Mail's own client id is in
  `/etc/veltos/mail-oauth.json` (`{"microsoft": {"client_id": "..."}}`).
  VeltOS has no registration yet, so such accounts are not offered (the
  add-account page says so and links to Outlook on the web); Gmail works
  with an app password.

## Tests

`tests/test_core.py` (folders, FETCH answers, MIME, HTML cleaning, building
messages, providers, the stores), `tests/test_sync.py` and
`tests/test_ui.py` (the sync engine and the window offscreen in English
and Turkish) against `tests/fakeserver.py`, an in-memory IMAP/SMTP **test
double** used only by the tests.

## Not yet

OAuth registration (see above), drafts saved on the server, folders made
or renamed from the app, conversations (threads), calendar invitations,
contacts beyond the people you got mail from, printing.
