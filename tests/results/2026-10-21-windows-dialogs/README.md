# 2026-10-21 — Windows 11 dialogs (live VM, QEMU/KVM, UEFI, no 3D)

Screenshots taken in the live session of ISO `veltos-0.1.0-dev-20261021-163819`
with the rebuilt packages of 2026-10-21 (evening) installed (`dpkg -i`).

| File | What it shows |
|---|---|
| `file-dialog-open.png` | `veltos-explorer --pick` (Open, "Pictures" filter): Windows 11's Open dialog built from File Explorer's parts |
| `firefox-open-file-through-portal.png` | Firefox's Ctrl+O arriving in the VeltOS dialog through xdg-desktop-portal ("Open File - Mozilla Firefox", All Files) |
| `password-prompt-wrong-password.png` | `pkexec /bin/true` from the session: the VeltOS User Account Control prompt (veltos-auth) after a wrong password; the right one was accepted afterwards (polkit journal: "successfully authenticated as unix-user:velt") |
| `sign-in-screen-wayland-greeter.png` | SDDM greeter in KWin on Wayland (`DisplayServer=wayland`), the whole 1920×1080 screen; signing in with the password started the session |
| `konsole-save-as-through-portal-theme.png` | Konsole's "Save Output" with `QT_QPA_PLATFORMTHEME=xdgdesktopportal`: the VeltOS Save As dialog ("Save as type: Plain text document") |
| `libreoffice-open-through-portal-theme.png` | LibreOffice Writer's Ctrl+O through the same theme, one dialog after the backend merges LibreOffice's duplicate request; the chosen file opened |
| `password-prompt-shield-icon.png` | The prompt with the final icon (VeltOS V centred on a shield, padlock badge) in its band, title bar and taskbar; cancelled with Esc |
| `firefox-download-panel-taskbar-progress.png` | Firefox downloading a 40 MB file from a slow local server: the restyled downloads panel, the thin progress bar under the taskbar icon with the count badge, Plasma's job notification |
| `taskbar-search-window.png` | The taskbar search box's window with "calc" typed: Best match list, Calculator card with Open |
| `clock-alarm-page.png` | VeltOS Clock, Alarm page (Focus sessions, Timer, Stopwatch and World clock were opened too) |
| `clock-alarm-notification.png` | The alarm "Tea time" ringing through `veltos-clock-agent` with the app closed: notification with Snooze and Dismiss (the sound played through pw-play) |
| `start-menu-clock-pinned-7zip.png` | Start after the checks: Clock pinned with its icon, 7-Zip's entries under All > Other |
| `windows-program-done-page.png` | `veltos-run` after 7-Zip 26.04's installer finished: the new Start entries with Open buttons, Done at the bottom right, the App Installer icon in the taskbar |
| `text-size-150-settings.png` | Settings with text size 150 % |
| `text-size-150-explorer.png` | File Explorer's Home with text size 150 % (tiles and Recent columns scaled) |

Not in pictures: adding a user from the Settings backend inside the
session (created with its password), the installer slideshow loading with
Calamares' QML module.
