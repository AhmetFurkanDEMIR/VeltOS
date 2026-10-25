# VeltOS AI (2026-10-25, dev VM)

Item 22 of the product owner's 2026-10-23 list: a Copilot-like assistant
pane with ChatGPT, Claude, Gemini and Copilot on the user's own API keys,
able to act on the system.

| Picture | What it shows |
|---|---|
| `pane-first-start-settings.png` | First start (no key): the pane on the right edge (a layer-shell surface with an exclusive zone), the maximised Weather window made room for it; "Yapay zekânızı seçin": ChatGPT (OpenAI), Claude (Anthropic), Gemini (Google), Copilot (Microsoft Azure OpenAI), the key field, model, "Modelleri göster", the actions switch and where the key is kept |
| `pane-closed-with-win-c.png` | Windows + C pressed: the pane closed and the window took the full width again |
| `stand-in-system-info.png` | A question answered with a read-only action ("Bu bilgisayarın ayrıntılarına bak", run at once) and a Markdown answer |
| `stand-in-action-asks.png` | "Açık moda geç": the action waits for "İzin ver" / "İzin verme" |
| `stand-in-light-mode-done.png` | "İzin ver": the system switched to light mode for real (`LookAndFeelPackage=org.veltos.light`), the action shows "Yapıldı" |
| `stand-in-light-pane-asks.png`, `stand-in-dark-mode-done-pane-follows.png` | Started in the light theme; "Koyu moda geç" allowed: the system went dark and the pane's colours followed at once |
| `app-icon.png` | The app icon: the VeltOS "V" (centred) with the AI sparkles, on light, dark and blue |

**How this was tested.** There is no API key of any of the services on the
development machine, so the conversations in the pictures come from a
stand-in service (`ai-demo.py`, using the package tests' `fakeservice.py`)
that answers in Claude's stream format; the pane, the approval flow and the
actions (VeltOS Settings' own light/dark switch) are the real ones. The
requests to each service (URL, headers, body), their stream formats with
tool calls, the history each service needs back (Claude's thinking blocks
with signatures, OpenAI's reasoning items, Gemini's thought signatures),
errors (401, network) and model lists are covered by the package tests
against the services' documented formats.

**Not tested:** a real conversation with OpenAI, Anthropic, Google or Azure
OpenAI (needs the owner's keys); Windows + C after a new sign-in (it worked
in the running session).
