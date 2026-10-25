# Taskbar date follows the language (2026-10-25, dev VM)

Item 26 of the product owner's 2026-10-23 list. QEMU dev VM, live system
of the 2026-10-23 ISO with this change's `veltos-settings`.

| Picture | What it shows |
|---|---|
| `before-desktop.png`, `before-taskbar-date.png` | Before: Turkish chosen as the display language the way Settings wrote it (only `[Translations] LANGUAGE=tr`), signed in again: everything Turkish, the taskbar still "12:51 PM 10/25/2026" |
| `settings-turkish-chosen.png` | Now: Settings > Time & language > Language & region, "Türkçe" chosen; the regional format follows ("Türkçe (Türkiye)"), the page says to sign in again |
| `after-taskbar-date.png` | After signing in again: "12:56 25.10.2026" |
| `after-calendar-flyout.png` | The calendar flyout: "25 Ekim Pazar", "Ekim 2026", Turkish weekdays |

What Settings writes now (read from `~/.config/plasma-localerc` in the
VM): `[Translations] LANGUAGE=tr` and, because the formats were those of
the old language (`en_US` for English, Windows' "Recommended" format),
`[Formats]` `LANG` and every `LC_*` key Plasma's startplasma exports
(`LC_TIME`, `LC_NUMERIC`, `LC_MONETARY`, ...) set to `tr_TR.UTF-8`; formats
the user had chosen themselves stay. Writing all the keys also beats
`LC_*` lines the installer may put into `/etc/default/locale` (startplasma
only exports the keys the file has).
