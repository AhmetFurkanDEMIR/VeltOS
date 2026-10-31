"""The local model's tool calls (llama-server's Chat Completions stream),
the actions added on 2026-10-27 and the commands VeltOS AI recognises
itself (intents.py). Stand-ins only: no model, no network, nothing on the
system is changed."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from veltos_ai import intents, local, providers, strings, tools  # noqa: E402
import fakeservice as fake  # noqa: E402


def chunks(*deltas, finish="stop"):
    events = [{"choices": [{"index": 0, "delta": delta, "finish_reason": None}]} for delta in deltas]
    events.append({"choices": [{"index": 0, "delta": {}, "finish_reason": finish}]})
    return fake.sse(events + ["[DONE]"])


class FixedServer:
    def base(self, _model):
        return "http://127.0.0.1:1"


class LocalToolTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        (self.folder / "Qwen3.5-2B-UD-Q5_K_XL.gguf").write_bytes(b"x")
        self.adapter = providers.Local({}, server=FixedServer())
        self.adapter.local = SimpleNamespace(model_path=lambda name: self.folder / name,
                                             DownloadError=local.DownloadError)

    def test_tool_call_in_pieces_and_its_result(self):
        answer = chunks({"role": "assistant", "content": None},
                        {"tool_calls": [{"index": 0, "id": "c1", "type": "function",
                                         "function": {"name": "set_theme", "arguments": ""}}]},
                        {"tool_calls": [{"index": 0, "function": {"arguments": "{\"mode\": "}}]},
                        {"tool_calls": [{"index": 0, "function": {"arguments": "\"dark\"}"}}]}, finish="tool_calls")
        service = fake.FakeService(answer)
        history = []
        self.adapter.add_user(history, "Koyu moda geç")
        events = list(providers.stream(self.adapter, history, "SYSTEM", tools.TOOLS, service))
        self.assertIn(("tool", {"id": "c1", "name": "set_theme", "input": {"mode": "dark"}}), events)
        body = service.requests[0]["body"]
        self.assertEqual(body["chat_template_kwargs"], {"enable_thinking": False})
        self.assertTrue(body["messages"][0]["content"].startswith("SYSTEM"))
        self.assertEqual({t["function"]["name"] for t in body["tools"]}, set(tools.BY_NAME))
        self.assertEqual(self.adapter.turn[0]["tool_calls"][0]["function"],
                         {"name": "set_theme", "arguments": "{\"mode\": \"dark\"}"})
        history.extend(self.adapter.turn)
        self.adapter.add_tool_results(history, [({"id": "c1"}, '{"ok": true}', False)])
        self.assertEqual(history[-1], {"role": "tool", "tool_call_id": "c1", "content": '{"ok": true}'})

    def test_plain_answer_and_history_start(self):
        service = fake.FakeService(chunks({"content": "Merhaba"}, {"content": "!"}))
        history = []
        self.adapter.add_user(history, "Merhaba")
        events = list(providers.stream(self.adapter, history, "S", [], service))
        self.assertEqual("".join(p for k, p in events if k == "text"), "Merhaba!")
        self.assertNotIn("tools", service.requests[0]["body"])
        # Old messages are dropped from a user message on, never from a tool result.
        long = [{"role": "user", "content": "a"}, {"role": "assistant", "tool_calls": []},
                {"role": "tool", "content": "x"}, {"role": "user", "content": "b"}]
        self.assertEqual(providers.trimmed(long, 2), [{"role": "user", "content": "b"}])

    def test_history_fits_the_local_model(self):
        # A fixed 24 messages were mostly action results after a few actions
        # and the model lost the thread (2026-10-31): the conversation is cut
        # by size, old action results shortened first.
        result = {"role": "tool", "tool_call_id": "c0", "content": "x" * 3000}
        call = {"role": "assistant", "content": "", "tool_calls": [{"id": "c0", "type": "function"}]}
        history = [{"role": "user", "content": "first"}, call, result, {"role": "assistant", "content": "done"}]
        for n in range(40):
            history += [{"role": "user", "content": f"question {n}"}, {"role": "assistant", "content": "answer " * 20}]
        history.append({"role": "user", "content": "now"})
        sent = providers.trimmed(history)
        self.assertEqual(sent[-1], {"role": "user", "content": "now"})
        self.assertEqual(sent[0]["role"], "user")
        self.assertGreater(len(sent), 24)
        self.assertLessEqual(sum(providers.size(m) for m in sent), providers.HISTORY_CHARS)
        short = providers.trimmed([{"role": "user", "content": "a"}, call, result, {"role": "user", "content": "b"}])
        self.assertEqual(short[2]["content"], "x" * providers.OLD_RESULT_CHARS + " …")
        self.assertEqual(len(result["content"]), 3000)              # the history itself is not changed
        # The current exchange (the last user message on) is sent whole.
        current = providers.trimmed([{"role": "user", "content": "q"}, call, result])
        self.assertEqual(current[-1]["content"], "x" * 3000)

    def test_default_model(self):
        self.assertEqual(providers.PROVIDERS["local"]["model"], local.DEFAULT_MODEL["file"])


class NewActionTests(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp()).resolve()
        os.environ["HOME"] = str(self.home)
        self.started, self.ran = [], []

    def runner(self, command, timeout=30):
        self.ran.append(command)
        return 0, ""

    def run_tool(self, name, arguments, **kwargs):
        checked = tools.validate(name, arguments)
        self.assertIsNotNone(checked, (name, arguments))
        ok, output = tools.execute(name, checked, "en", self.started.append, self.runner, **kwargs)
        return ok, json.loads(output)

    def test_every_action_has_titles(self):
        for name, arguments in (("set_night_light", {"on": True}), ("set_power_mode", {"mode": "power-saver"}),
                                ("set_brightness", {"percent": 40}), ("set_airplane_mode", {"on": False}),
                                ("list_wifi_networks", {}), ("connect_wifi", {"name": "Ev"}),
                                ("set_wallpaper", {"path": "/x.png"}), ("set_timezone", {"zone": "Europe/Istanbul"}),
                                ("power", {"action": "restart"}), ("install_app", {"package": "vlc"}),
                                ("uninstall_app", {"package": "vlc"}), ("install_updates", {}),
                                ("create_folder", {"path": "a"}), ("move_to_recycle_bin", {"path": "a"}),
                                ("empty_recycle_bin", {}), ("open_file", {"path": "a"}),
                                ("read_text_file", {"path": "a"}), ("write_text_file", {"path": "a", "text": ""}),
                                ("run_command", {"command": "uname -r", "administrator": True})):
            for lang in ("en", "tr"):
                title = tools.title(name, tools.validate(name, arguments), lang)
                self.assertNotEqual(title, name, (name, lang))
        self.assertIn("uname -r", tools.title("run_command", {"command": "uname -r", "administrator": True}, "tr"))
        self.assertFalse(tools.needs_approval("list_wifi_networks"))
        self.assertTrue(tools.needs_approval("read_text_file"))       # a file's contents go to the service
        self.assertTrue(tools.needs_approval("run_command"))

    def test_files_stay_in_the_home_folder(self):
        ok, out = self.run_tool("create_folder", {"path": "Desktop/Notlar"})
        self.assertTrue(ok)
        self.assertTrue((self.home / "Desktop/Notlar").is_dir())
        self.assertFalse(self.run_tool("create_folder", {"path": "/etc/x"})[0])
        self.assertFalse(self.run_tool("create_folder", {"path": "../outside"})[0])
        ok, _ = self.run_tool("write_text_file", {"path": "notes.txt", "text": "liste"})
        self.assertTrue(ok)
        self.assertFalse(self.run_tool("write_text_file", {"path": "notes.txt", "text": "yeni"})[0])
        self.assertTrue(self.run_tool("write_text_file", {"path": "notes.txt", "text": "yeni", "overwrite": True})[0])
        ok, out = self.run_tool("read_text_file", {"path": "notes.txt"})
        self.assertEqual((ok, out["text"]), (True, "yeni"))
        (self.home / "bin.dat").write_bytes(b"\0\1\2")
        self.assertFalse(self.run_tool("read_text_file", {"path": "bin.dat"})[0])
        self.assertFalse(self.run_tool("read_text_file", {"path": "/etc/passwd"})[0])
        self.assertTrue(self.run_tool("move_to_recycle_bin", {"path": "notes.txt"})[0])
        self.assertEqual(self.ran[-1], ["gio", "trash", str(self.home / "notes.txt")])
        self.assertFalse(self.run_tool("move_to_recycle_bin", {"path": "."})[0])     # never the home folder
        self.assertTrue(self.run_tool("open_file", {"path": "bin.dat"})[0])
        self.assertEqual(self.started[-1], ["xdg-open", str(self.home / "bin.dat")])

    def test_packages_go_through_packagekit(self):
        old = tools.lists_old
        tools.lists_old = lambda: False
        try:
            self.assertTrue(self.run_tool("install_app", {"package": "VLC"})[0])
            self.assertEqual(self.ran[-1][-4:], ["pkcon", "-p", "install", "vlc"])
            self.assertEqual(self.ran[-1][1:3], ["-m", "veltos_store.ptyrun"])
            self.assertFalse(self.run_tool("install_app", {"package": "vlc; rm -rf /"})[0])
            self.assertTrue(self.run_tool("install_updates", {})[0])
            self.assertEqual([c[-1] for c in self.ran[-2:]], ["refresh", "update"])
        finally:
            tools.lists_old = old
        self.assertEqual(tools.pkcon(["install", "x"], lambda c, timeout=0: (1, "Fatal error: Not authorized\n")),
                         (False, "Not authorized"))
        self.assertEqual(tools.pkcon(["update"], lambda c, timeout=0: (5, "Nothing to do\n")), (True, ""))

    def test_commands_and_power(self):
        commands = []

        def command_runner(command, administrator):
            commands.append((command, administrator))
            return 0, "6.12.48+deb13-amd64\n"
        ok, out = self.run_tool("run_command", {"command": "uname -r"}, command_runner=command_runner)
        self.assertEqual((ok, out["output"]), (True, "6.12.48+deb13-amd64\n"))
        self.run_tool("run_command", {"command": "apt-get update", "administrator": True}, command_runner=command_runner)
        self.assertEqual(commands[-1], ("apt-get update", True))
        ok, out = self.run_tool("run_command", {"command": "x", "administrator": True},
                                command_runner=lambda c, a: (126, ""))
        self.assertIn("password", out["error"])
        code, output = tools.run_command("echo hello; echo oops >&2; exit 3")
        self.assertEqual((code, output), (3, "hello\noops\n"))
        self.run_tool("power", {"action": "lock"})
        self.assertEqual(self.started[-1], ["loginctl", "lock-session"])
        self.assertIsNone(tools.validate("power", {"action": "format_disk"}))

    def test_brightness(self):
        answers = {"get-property": (0, "i 255\n"), "call": (0, "")}

        def runner(command, timeout=30):
            self.ran.append(command)
            return answers[command[2]] if command[0] == "busctl" else (1, "")
        self.assertTrue(tools.set_brightness(40, runner))
        self.assertEqual(self.ran[-1][-3:], ["iu", "102", "0"])


class IntentTests(unittest.TestCase):
    APPS = {"hesap makinesi": "Hesap Makinesi", "not defteri": "Not Defteri", "firefox": "Firefox",
            "calculator": "Calculator"}

    def find(self, name, lang="en"):
        return (Path("x.desktop"), self.APPS[name]) if name in self.APPS else None

    def test_commands(self):
        cases = {
            "Koyu moda geç": ("set_theme", {"mode": "dark"}),
            "Karanlık moda al": ("set_theme", {"mode": "dark"}),
            "Açık temaya dön": ("set_theme", {"mode": "light"}),
            "Switch to dark mode": ("set_theme", {"mode": "dark"}),
            "Wi-Fi'ı kapat": ("set_wifi", {"on": False}),
            "WiFi aç": ("set_wifi", {"on": True}),
            "turn off wifi": ("set_wifi", {"on": False}),
            "Bluetooth'u kapatır mısın": ("set_bluetooth", {"on": False}),
            "Gece ışığını aç": ("set_night_light", {"on": True}),
            "Uçak modunu aç": ("set_airplane_mode", {"on": True}),
            "Parlaklığı %40 yap": ("set_brightness", {"percent": 40}),
            "Ses düzeyini 30 yap": ("set_volume", {"percent": 30}),
            "Sesi kapat": ("set_mute", {"muted": True}),
            "Hesap makinesini aç": ("open_app", {"name": "Hesap Makinesi"}),
            "Not Defteri'ni aç": ("open_app", {"name": "Not Defteri"}),
            "Open Firefox": ("open_app", {"name": "Firefox"}),
            "VLC yükle": ("install_app", {"package": "vlc"}),
            "install gimp": ("install_app", {"package": "gimp"}),
            "Güncellemeleri yükle": ("install_updates", {}),
            "Ekranı kilitle": ("power", {"action": "lock"}),
            "Ekran görüntüsü al": ("take_screenshot", {}),
            "Güç tasarrufu moduna geç": ("set_power_mode", {"mode": "power-saver"}),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(intents.match(text, "tr", self.find), expected)
                self.assertIsNotNone(tools.validate(*expected))

    def test_not_commands(self):
        for text in ("Wi-Fi açık mı?", "Türkiye'nin başkenti neresi?", "Merhaba, nasılsın?", "Kapıyı aç",
                     "is bluetooth on", "Bana koyu mod ile açık mod arasındaki farkı uzun uzun anlatır mısın lütfen",
                     ""):
            with self.subTest(text=text):
                self.assertIsNone(intents.match(text, "tr", self.find))

    def test_turkish_letters(self):
        self.assertEqual(intents.fold("İNDİR ışık"), "indir ışık")
        self.assertEqual(tools.loose("Inkscape"), tools.loose("ınkscape"))
        self.assertEqual(strings.text("tr", "act_set_theme_dark"), "Koyu moda geç")


if __name__ == "__main__":
    unittest.main()
