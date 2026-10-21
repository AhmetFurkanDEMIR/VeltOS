# veltos-auth — VeltOS authentication prompt

The password window for administrator actions, in the layout of Windows
11's User Account Control prompt. It is a polkit authentication agent:
whenever a program needs an administrator's permission (installing apps
from the Store, adding users, changing the time zone, `pkexec`), polkit
asks the session's agent, and this one shows the VeltOS window instead of
KDE's.

| Part | What |
|---|---|
| `veltos_auth/agent.py` (`veltos-auth-agent`) | The D-Bus object polkit calls (`org.freedesktop.PolicyKit1.AuthenticationAgent`), registered for the login session; GLib only. One prompt process per request; answers polkit's call when the prompt ends. |
| `veltos_auth/dialog.py` + `qml/Main.qml` | The window (PySide6/QML): shield band, the question polkit sends, the program and its details, the administrator's picture, the password box, Yes/No. English and Turkish. |
| `veltos_auth/helper.py` | The line protocol of polkit's setuid helper `polkit-agent-helper-1`, which checks the password through PAM and tells polkit the result. The password never leaves the prompt process except through that helper. |
| `veltos_auth/users.py` | The accounts that may answer (polkit identities, groups expanded), their pictures (AccountsService, `~/.face.icon`, the VeltOS default), the program name and the action's description from its `.policy` file. |
| `data/veltos-auth-agent.service` | Started with the Plasma session (`plasma-core.target.wants`), like KDE's agent. KDE's `plasma-polkit-agent.service` is masked by this package (`debian/veltos-auth.links`). |

Tests (`tests/`): the helper protocol, request mapping, subject
selection, and the window loaded offscreen with a stand-in helper
(`fake_helper.py`): a wrong password keeps the window open with the
message, the right one ends with `SUCCESS`; cancelling prints `CANCELLED`.

Limits: the window is not kept above other windows by KWin (it is a
normal dialog); polkit's "Details" are shown as they come.
