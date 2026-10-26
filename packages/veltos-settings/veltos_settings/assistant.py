"""Apps > VeltOS AI: the assistant's service, API key, model and whether it
may act on the PC, in VeltOS Settings (product owner, 2026-10-26).

The settings are VeltOS AI's own (veltos-ai's `config` module, the mode-600
file ~/.config/veltos/ai.json); a running pane reads them again when it is
opened. Keys never go to QML: the page only learns whether a service has
one. Without veltos-ai installed the page says so.
"""

try:
    from veltos_ai import config as ai_config
    from veltos_ai.providers import ORDER, PROVIDERS
except ImportError:  # veltos-ai is a Recommends of veltos-settings
    ai_config = None
    ORDER, PROVIDERS = (), {}


class Assistant:
    def __init__(self, config_module=None, file=None):
        self.config = config_module if config_module is not None else ai_config
        self.file = file

    @property
    def available(self):
        return self.config is not None

    def state(self):
        if not self.available:
            return {"available": False, "provider": "", "providers": [], "services": {}, "actions": True,
                    "ready": False}
        data = self.config.load(self.file)
        return {
            "available": True,
            "provider": data.get("provider", ""),
            "providers": [{"value": name, "label": PROVIDERS[name]["title"], "keysUrl": PROVIDERS[name]["keys"],
                           "defaultModel": PROVIDERS[name]["model"]} for name in ORDER],
            "services": {name: {"hasKey": bool(data["services"][name].get("key")),
                                "model": data["services"][name].get("model", ""),
                                "endpoint": data["services"][name].get("endpoint", "")}
                         for name in ORDER},
            "actions": bool(data.get("actions", True)),
            "ready": bool(self.config.ready(data)),
        }

    def _change(self, change):
        if not self.available:
            return False
        data = self.config.load(self.file)
        if change(data) is False:
            return False
        try:
            self.config.save(data, self.file)
        except OSError:
            return False
        return True

    def save_service(self, name, key, model, endpoint):
        """The service's key (an empty one keeps the saved key), model and
        Azure endpoint; the service becomes the chosen one."""
        if name not in PROVIDERS:
            return False

        def change(data):
            entry = data["services"][name]
            if key.strip():
                entry["key"] = key.strip()
            entry["model"] = model.strip() or PROVIDERS[name]["model"]
            entry["endpoint"] = endpoint.strip()
            data["provider"] = name
        return self._change(change)

    def remove_key(self, name):
        if name not in PROVIDERS:
            return False
        return self._change(lambda data: data["services"][name].update(key=""))

    def set_actions(self, allowed):
        return self._change(lambda data: data.update(actions=bool(allowed)))
