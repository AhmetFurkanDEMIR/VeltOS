# veltos-auth — VeltOS authentication prompt

The password window for administrator actions, in the layout of Windows
11's User Account Control prompt. It is a polkit authentication agent:
whenever a program needs an administrator's permission (installing apps
from the Store, adding users, changing the time zone, `pkexec`), polkit
asks the session's agent, and this one shows the VeltOS window instead of
KDE's.

| Part | What |
|---|---|
| `veltos_auth/agent.py` (`veltos-auth-agent`) | The D-Bus object polkit calls (`org.freedesktop.PolicyKit1.AuthenticationAgent`), registered for the login session; GLib only. One prompt process per request; answers polkit's call when the prompt ends. It registers with the session's full locale (`strings.polkit_locale`, e.g. `tr_TR.UTF-8` rather than `tr`), so the messages polkit passes on ("Authentication is required to ...") come in the session language (product owner, 2026-10-22). |
| `veltos_auth/dialog.py` + `qml/Main.qml` | The window (PySide6/QML): shield band, the question polkit sends, the program and its details, the administrator's picture, the password box, OK/Cancel (product owner, 2026-10-22, instead of Windows' own Yes/No). English and Turkish. The password box is in the Tab order and shows the text (I-beam) pointer; an action icon the icon theme does not have (e.g. `system-users`) falls back to the VeltOS shield. |
| `veltos_auth/helper.py` | The line protocol of polkit's setuid helper `polkit-agent-helper-1`, which checks the password through PAM and tells polkit the result. The password never leaves the prompt process except through that helper. |
| `veltos_auth/users.py` | The accounts that may answer (polkit identities, groups expanded), their pictures (AccountsService, `~/.face.icon`, the VeltOS default), the program name and the action's description from its `.policy` file. The program that asks is shown with its name and icon like Windows' prompt: from `polkit.subject-pid` up through the parent processes to the first one started from an app's desktop file (VeltOS Store when it installs through pkcon); the action's own icon only when none is found. |
| `data/veltos-auth-agent.service` | Started with the Plasma session (`plasma-core.target.wants`), like KDE's agent. KDE's `plasma-polkit-agent.service` is masked by this package (`debian/veltos-auth.links`). |

Tests (`tests/test_auth.py`): the helper protocol, request mapping,
subject selection, the button texts, the locale given to polkit, and the
window loaded offscreen with a stand-in helper (`fake_helper.py`): a
wrong password keeps the window open with the message, the right one ends
with `SUCCESS`; cancelling prints `CANCELLED`.

Limits: the window is not kept above other windows by KWin (it is a
normal dialog); polkit's "Details" are shown as they come.

## Password reset USB

A forgotten password can be set again on the sign-in screen with a USB
flash drive made for the account (`veltos_auth/recovery.py`,
`/usr/libexec/veltos/password-recovery`).

- The drive holds the key: `VeltOS Password Reset/<pc>-<user>.veltoskey`
  (JSON: user, PC name, 256 random bits as 52 base32 letters) and a
  README. Nothing on the drive is formatted or removed.
- The PC keeps only an scrypt hash of the key with a random salt:
  `/var/lib/veltos/recovery/<user>.json` (mode 600; the folder is readable
  so Settings can tell whether a drive exists).
- `password-recovery drives` lists USB/removable partitions with a file
  system (never the live medium, a mounted system disk or the disk being
  installed onto); `status USER`; `create USER PARTITION [--root DIR]
  [--host NAME] [--exclude DISK,...]` and `remove USER` need root (the
  installer's job; Settings through pkexec and the polkit action
  `org.veltos.password-recovery`, auth_admin_keep).
- The sign-in screen cannot run programs: `veltos-password-recovery.socket`
  (127.0.0.1:47824, Accept=yes) starts `password-recovery serve` per
  connection, which answers only connections whose socket belongs to the
  `sddm` user (looked up in /proc/net/tcp): `POST /status` (has a drive,
  the account's PasswordHint from AccountsService), `/find` (a drive with a
  matching key is inserted) and `/reset` (finds the key again, then
  `chpasswd` and the new hint). Anyone holding the drive can reset that
  account's password, as with Windows' password reset disk. Disk
  encryption keeps its own password.
- Tests: `tests/test_recovery.py` (fake lsblk/mount/chpasswd, a stand-in
  socket and TCP table).

## The lock screen's requests (2026-11-02)

The lock screen (the user's own kscreenlocker greeter) cannot reach the
network. `password-recovery status-self` prints the caller's own account,
whether it has a reset USB and its hint (AccountsService's PasswordHint
over the system bus); `password-recovery want-reset` asks the service
(`POST /want-reset`, accepted only from a process of that same account)
to open the sign-in screen's reset panel for it. The service keeps the
wish in `/run/veltos-password-recovery/<user>` for five minutes; the
sign-in screen's `/status` answers `resetRequested` once. The reset itself
still needs the USB key and the sign-in screen's own connection.
