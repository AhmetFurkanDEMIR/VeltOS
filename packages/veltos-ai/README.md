# veltos-ai — VeltOS AI

An assistant pane in the manner of Windows 11's Copilot (PySide6/QML):
Windows + C (or the Start entry) opens it on the right edge of the screen
and closes it again.

- **The pane** is a layer-shell surface (`org.kde.layershell`, package
  qml6-module-org-kde-layershell): anchored to the top, bottom and right,
  above windows, with an exclusive zone of its width, so maximised windows
  make room as they did for Copilot. Escape or ✕ closes it; the process
  stays for the next Windows + C and ends after ten idle minutes. One pane
  per user: a second `veltos-ai` hands "toggle" to the running one (local
  socket `veltos-ai-UID`).
- **Services** (`providers.py`, plain HTTPS with urllib: the image takes
  packages from Debian only, which has none of the services' SDKs):
  - ChatGPT: OpenAI's Responses API (`/v1/responses`, `store: false`); the
    newest GPT models call tools only there (OpenAI's changelog, checked
    2026-10-25). Default model `gpt-5.5`; "Show models" lists the account's.
  - Claude: Anthropic's Messages API, `anthropic-version: 2026-10-21`,
    default `claude-opus-5-5`; client tools stream their input
    (`eager_input_streaming`) and are checked before they run; declined
    requests are retried server-side (`fallbacks: "default"`, beta
    `server-side-fallback-2026-07-01`) for the Opus, Sonnet 5.5 and Fable
    models.
  - Gemini: Google's `streamGenerateContent` (`alt=sse`), default
    `gemini-flash-latest` (the alias of the newest Flash).
  - Copilot: Microsoft's consumer Copilot has no API key for personal use;
    this choice uses Microsoft's Azure OpenAI (Foundry) v1 API at
    `https://<resource>.openai.azure.com/openai/v1/` with the user's key and
    deployment, and says so in the pane.
  Every answer streams in and is shown with Markdown. The turn is kept as
  the service sent it (thinking blocks with signatures, reasoning items,
  thought signatures) and sent back with tool results, as the services
  require.
- **Actions** (`tools.py`): a fixed list, never a shell. Read-only ones run
  at once (the PC's details, finding files by name); everything else waits
  for "Allow": light/dark mode, volume, mute, Wi-Fi, Bluetooth, Do not
  disturb (through VeltOS Settings' own helpers), opening an app, a
  Settings page, a folder in File Explorer (known folders or inside the
  home folder), a web page (http/https only), Snipping Tool. Settings can
  turn actions off. Stopping an answer while an action waits still gives
  the service a result for each call.
- **Settings**: the service, its key, model and (Azure) endpoint, kept in
  `~/.config/veltos/ai.json` with mode 600 (readable only by the user; not
  encrypted: the session has no unlocked secret store, KWallet would ask
  for its own password). Messages go only to the chosen service.
- The pane follows light/dark and the accent at once (it can switch the
  theme itself). English and Turkish.

## Tests

`tests/test_ai.py`: each service's request (URL, headers, body) and stream
with a tool call (`tests/fakeservice.py`), the history each needs back,
a refusal and a cut-off tool input, Azure's URL, errors (401, network,
429, unknown model), model lists and the default choice; the actions'
checks, titles in both languages, running them (http/https only, folders
inside the home folder, Settings' helpers through a stand-in), finding
apps and files; settings saved with mode 600; the backend's conversation
with "Allow", "Don't allow", Stop, actions turned off, errors, refusals,
the live theme. `tests/test_ui.py`: the pane offscreen in English and
Turkish (settings without a key, a conversation with an action, a narrow
pane); any QML warning fails.

Not tested here: real conversations with the services (no keys on the
development machine; `tests/results/2026-10-25-veltos-ai/`).
