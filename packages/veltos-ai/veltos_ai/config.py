"""VeltOS AI's settings: the chosen service, and per service the API key,
the model and (Azure) the endpoint.

They are kept in ~/.config/veltos/ai.json with mode 600: only the user's
account can read the keys. The file is not encrypted (the session has no
unlocked secret store to rely on: KWallet asks for its own password on
first use), which the panel says next to the key field.
"""

import json
import os
from pathlib import Path

from .providers import ORDER, PROVIDERS


def path():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "veltos" / "ai.json"


def load(file=None):
    file = Path(file or path())
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("provider", "")
    services = data.get("services") if isinstance(data.get("services"), dict) else {}
    for name in ORDER:
        entry = services.get(name) if isinstance(services.get(name), dict) else {}
        entry.setdefault("key", "")
        entry.setdefault("model", PROVIDERS[name]["model"])
        entry.setdefault("endpoint", "")
        services[name] = entry
    data["services"] = services
    data.setdefault("actions", True)
    return data


def save(data, file=None):
    """Writes the settings readable by the user only (mode 600 from the
    start: the key is never in a file others can read)."""
    file = Path(file or path())
    file.parent.mkdir(parents=True, exist_ok=True)
    tmp = file.with_suffix(".tmp")
    descriptor = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, file)


def ready(data):
    """Whether the chosen service can be used (key, and Azure's endpoint and deployment)."""
    name = data.get("provider")
    if name not in PROVIDERS:
        return False
    entry = data["services"][name]
    if name == "local":
        from . import local
        return local.engine_available() and local.model_path(entry.get("model", "")) is not None
    if not entry.get("key"):
        return False
    if name == "copilot":
        return bool(entry.get("endpoint") and entry.get("model"))
    return True
