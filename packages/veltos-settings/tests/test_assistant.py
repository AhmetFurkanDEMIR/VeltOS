"""Tests for Settings' VeltOS AI page backend (assistant.py) with a
stand-in for veltos-ai's config module (veltos-ai is another package)."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_settings import assistant  # noqa: E402

PROVIDERS = {
    "local": {"title": "Local model (free, offline)", "model": "gemma.gguf", "keys": ""},
    "openai": {"title": "ChatGPT (OpenAI)", "model": "gpt-5.5", "keys": "https://platform.openai.com/api-keys"},
    "claude": {"title": "Claude (Anthropic)", "model": "claude-opus-5-5", "keys": "https://platform.claude.com/"},
    "copilot": {"title": "Copilot (Microsoft Azure OpenAI)", "model": "", "keys": "https://ai.azure.com/"},
}
ORDER = ("local", "openai", "claude", "copilot")


class FakeConfig:
    """veltos_ai.config: load() fills every service, save() keeps a copy."""

    def __init__(self):
        self.saved = {"provider": "", "actions": True,
                      "services": {n: {"key": "", "model": PROVIDERS[n]["model"], "endpoint": ""} for n in ORDER}}
        self.fail = False

    def load(self, file=None):
        return copy.deepcopy(self.saved)

    def save(self, data, file=None):
        if self.fail:
            raise OSError("read-only")
        self.saved = copy.deepcopy(data)

    def ready(self, data):
        name = data.get("provider")
        return name in PROVIDERS and bool(data["services"][name]["key"])


class FakeLocal:
    """veltos_ai.local: the downloaded model files."""

    def __init__(self, files=()):
        self.files = list(files)

    def installed(self):
        return [{"file": f, "size": 1} for f in self.files]


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.saved_tables = (assistant.PROVIDERS, assistant.ORDER)
        assistant.PROVIDERS, assistant.ORDER = PROVIDERS, ORDER
        self.config = FakeConfig()
        self.ai = assistant.Assistant(self.config, local_module=FakeLocal(["gemma.gguf"]))

    def tearDown(self):
        assistant.PROVIDERS, assistant.ORDER = self.saved_tables

    def test_state_never_contains_keys(self):
        self.config.saved["services"]["claude"]["key"] = "sk-ant-secret"
        self.config.saved["provider"] = "claude"
        state = self.ai.state()
        self.assertTrue(state["available"])
        self.assertTrue(state["ready"])
        self.assertTrue(state["services"]["claude"]["hasKey"])
        self.assertFalse(state["services"]["openai"]["hasKey"])
        self.assertNotIn("sk-ant-secret", repr(state))
        self.assertEqual([p["value"] for p in state["providers"]], list(ORDER))

    def test_save_service_chooses_it_and_keeps_an_old_key_when_none_is_typed(self):
        self.assertTrue(self.ai.save_service("openai", " sk-new ", "", ""))
        self.assertEqual(self.config.saved["provider"], "openai")
        self.assertEqual(self.config.saved["services"]["openai"]["key"], "sk-new")
        self.assertEqual(self.config.saved["services"]["openai"]["model"], "gpt-5.5")   # empty: the default
        self.assertTrue(self.ai.save_service("openai", "", "gpt-5.6", ""))
        self.assertEqual(self.config.saved["services"]["openai"]["key"], "sk-new")
        self.assertEqual(self.config.saved["services"]["openai"]["model"], "gpt-5.6")
        self.assertFalse(self.ai.save_service("evil", "k", "", ""))

    def test_local_model_is_counted_and_can_be_chosen(self):
        self.assertEqual(self.ai.state()["localModels"], 1)
        self.assertTrue(self.ai.use_local())
        self.assertEqual(self.config.saved["provider"], "local")
        self.assertFalse(self.ai.state()["services"]["local"]["hasKey"])

    def test_remove_key_and_actions(self):
        self.ai.save_service("claude", "sk-ant", "", "")
        self.assertTrue(self.ai.remove_key("claude"))
        self.assertEqual(self.config.saved["services"]["claude"]["key"], "")
        self.assertTrue(self.ai.set_actions(False))
        self.assertFalse(self.config.saved["actions"])
        self.config.fail = True
        self.assertFalse(self.ai.set_actions(True))

    def test_without_veltos_ai_the_page_says_so(self):
        missing = assistant.Assistant(None)
        missing.config = None
        self.assertFalse(missing.state()["available"])
        self.assertFalse(missing.save_service("openai", "k", "", ""))


if __name__ == "__main__":
    unittest.main()
