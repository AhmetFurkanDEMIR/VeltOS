# Crash notice in Windows 11's design (2026-10-25, dev VM)

Item 17 of the product owner's 2026-10-23 list.

| Picture | What it shows |
|---|---|
| `before-drkonqi-toast.png` | Before: KDE's DrKonqi toast ("Dr. Konqi", a red "!" picture, "Report Bug" and a cut-off "Restart Application"); DrKonqi also left a sad-face icon in the tray |
| `terminal-crash-notice.png` | After: Terminal (Konsole) crashed with SIGSEGV: the app's own name and icon, "Terminal beklenmedik şekilde kapandı", a short explanation, "Yeniden başlat" |
| `after-restart-terminal-back.png` | "Yeniden başlat" pressed: Terminal running again, in a unit of its own (`app-org.kde.konsole-49268.scope`) |
| `calculator-crash-notice.png` | The same for a VeltOS app (Calculator, a Python program, matched through its launcher) |

A crash of a background service (`kill -SEGV xembedsniproxy`) showed no
notice; the journal says "no app of the user, no notice". DrKonqi's tray
icon and window no longer appear.
