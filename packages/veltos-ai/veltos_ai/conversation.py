"""The conversation kept between starts of VeltOS AI.

A closed pane's process ends after ten idle minutes, and the chat went
with it: the next question started a conversation the model knew nothing
about (product owner, 2026-10-31). The panel's messages and what the
service was told (the history, in that service's own format) are kept in
~/.local/share/veltos-ai/conversation.json, readable by the user only,
until "New chat" clears them.
"""

import json
import os
from pathlib import Path

KINDS = ("user", "assistant", "action", "error")
MAX_MESSAGES = 200        # what the panel shows again
MAX_HISTORY = 400         # what the service is told again (actions take several entries)


def path():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "veltos-ai" / "conversation.json"


def load(file):
    """{"messages": [...], "history": [...], "provider": ""}; empty when the
    file is missing or not VeltOS AI's."""
    empty = {"messages": [], "history": [], "provider": ""}
    try:
        data = json.loads(Path(file).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty
    if not isinstance(data, dict):
        return empty
    messages = [m for m in data.get("messages") or [] if valid(m)]
    history = [h for h in data.get("history") or [] if isinstance(h, dict)]
    provider = data.get("provider") if isinstance(data.get("provider"), str) else ""
    for message in messages:
        settle(message)
    return {"messages": messages[-MAX_MESSAGES:], "history": history if provider else [], "provider": provider}


def valid(message):
    return (isinstance(message, dict) and isinstance(message.get("id"), int) and message.get("kind") in KINDS
            and isinstance(message.get("text", ""), str))


def settle(message):
    """A message that was still waiting when the panel ended cannot go on:
    an action not answered was not run, an answer being written stopped."""
    message.setdefault("text", "")
    message.setdefault("title", "")
    state = message.get("state") or ""
    if message["kind"] == "action" and state not in ("done", "failed", "denied"):
        message["state"] = "denied"
    elif message["kind"] == "assistant" and state == "streaming":
        message["state"] = "stopped"
    else:
        message["state"] = state if isinstance(state, str) else ""


def save(file, messages, history, provider):
    """Writes the conversation readable by the user only (mode 600 from the
    start, as the settings with the keys)."""
    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    data = {"messages": [{k: m.get(k) for k in ("id", "kind", "text", "state", "title")} for m in messages
                         ][-MAX_MESSAGES:],
            "history": cut_history(history), "provider": provider}
    tmp = file.with_suffix(".tmp")
    descriptor = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False))
    os.chmod(tmp, 0o600)
    os.replace(tmp, file)


def cut_history(history):
    """The newest MAX_HISTORY entries, starting at a user's own words: a
    tool result whose request was cut off would be refused."""
    if len(history) <= MAX_HISTORY:
        return list(history)
    recent = history[-MAX_HISTORY:]
    while recent and not plain_user(recent[0]):
        recent = recent[1:]
    return recent


def plain_user(entry):
    """A user message with the user's words (Claude and Gemini carry tool
    results in user turns too)."""
    if entry.get("role") != "user":
        return False
    content = entry.get("content", entry.get("parts"))
    if isinstance(content, str):
        return True
    return isinstance(content, list) and any(
        isinstance(part, dict) and (part.get("type") == "text" or "text" in part) for part in content)


def clear(file):
    try:
        Path(file).unlink()
    except OSError:
        pass
