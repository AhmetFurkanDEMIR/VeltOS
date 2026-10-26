# Language choice (2026-10-26, dev VM)

The live image currently compiles two display locales, `en_US.UTF-8` and
`tr_TR.UTF-8`; VeltOS apps provide English and Turkish translations. Regional
formats are a separate choice and may include other installed UTF-8 locales.
The Settings lists put Turkish and English first in both interfaces.

| Picture | What it shows |
|---|---|
| `language-list.png` | English Settings: Türkçe first, English (United States) second |
| `regional-list.png` | English Settings: Turkish (Türkiye) and American English first |
| `turkish-language-options.png` | Turkish Settings: Türkçe first, English second |
| `turkish-regional-options.png` | Turkish Settings: Turkish (Türkiye) first, American English second |
| `language-selected-tr.png` | Turkish selected; the page asks for a new sign-in |
| `language-turkish-settings.png` | Settings translated to Turkish after signing in again |
| `language-selected-en.png` | English selected; regional formats returned to en_US |
| `english-settings.png` | Settings translated to English after signing in again |

The session's `plasma-localerc` was checked after each choice. On the Turkish
sign-in, `LANGUAGE=tr@veltos:tr` was present in the Plasma session. Package
tests: veltos-settings (113); veltos-desktop (131, one skipped).
