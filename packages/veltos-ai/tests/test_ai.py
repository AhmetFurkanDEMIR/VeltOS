"""VeltOS AI without a window: the three APIs' requests and streams, the
tool list and its checks, settings on disk, and the backend's
conversation with an action that waits for "Allow" (stand-in services,
no network)."""

import json
import os
import stat
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
# One application object for every test module: the window tests need a
# QGuiApplication, so this module makes that kind too.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from veltos_ai import config, providers, strings, tools  # noqa: E402
import fakeservice as fake  # noqa: E402

TOOLS = [tools.BY_NAME["set_wifi"], tools.BY_NAME["get_system_info"]]


def run_stream(adapter, answer):
    service = fake.FakeService(answer)
    history = []
    adapter.add_user(history, "Turn on Wi-Fi")
    events = list(providers.stream(adapter, history, "system", TOOLS, service))
    return service.requests[0], history, events


class ProviderTests(unittest.TestCase):
    def test_sse(self):
        lines = [b"event: a\n", b"data: {\"x\": 1}\n", b"\n", b": comment\n", b"data: line1\n", b"data: line2\n", b"\n"]
        self.assertEqual(list(providers.sse_events(lines)), [("a", "{\"x\": 1}"), (None, "line1\nline2")])

    def test_claude(self):
        adapter = providers.adapter("claude", {"key": "sk-ant-test", "model": "claude-opus-5-5"})
        request, history, events = run_stream(adapter, fake.claude_tool_turn())
        self.assertEqual(request["url"], "https://api.anthropic.com/v1/messages")
        headers = {k.lower(): v for k, v in request["headers"].items()}
        self.assertEqual(headers["x-api-key"], "sk-ant-test")
        self.assertEqual(headers["anthropic-version"], "2026-10-21")
        self.assertEqual(headers["anthropic-beta"], "server-side-fallback-2026-07-01")
        body = request["body"]
        self.assertEqual((body["model"], body["stream"], body["fallbacks"]), ("claude-opus-5-5", True, "default"))
        self.assertNotIn("temperature", body)
        self.assertTrue(all(t["eager_input_streaming"] for t in body["tools"]))
        self.assertEqual(body["tools"][0]["input_schema"]["required"], ["on"])
        text = "".join(p for k, p in events if k == "text")
        self.assertEqual(text, "Turning on Wi-Fi.")
        calls = [p for k, p in events if k == "tool"]
        self.assertEqual(calls, [{"id": "toolu_1", "name": "set_wifi", "input": {"on": True}}])
        self.assertEqual(events[-1], ("end", {"stop": "tool_use"}))
        # The turn goes back unchanged: the thinking block with its signature.
        content = adapter.turn[0]["content"]
        self.assertEqual(content[0], {"type": "thinking", "thinking": "", "signature": "sig-1"})
        self.assertEqual(content[2]["input"], {"on": True})
        history.extend(adapter.turn)
        adapter.add_tool_results(history, [(calls[0], '{"ok": true}', False)])
        self.assertEqual(history[-1], {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_1", "content": '{"ok": true}', "is_error": False}]})
        # Haiku has no server-side fallback.
        haiku = providers.adapter("claude", {"key": "k", "model": "claude-haiku-5-5"})
        self.assertNotIn("fallbacks", json.loads(haiku.request([], "s", []).data))

    def test_claude_refusal_and_bad_json(self):
        adapter = providers.adapter("claude", {"key": "k"})
        _request, _history, events = run_stream(adapter, fake.claude_text("partial", stop="refusal"))
        self.assertEqual(events[-1], ("end", {"stop": "refusal"}))
        self.assertEqual(adapter.turn, [])
        broken = fake.claude_tool_turn().replace(b'ue}', b'ue')
        adapter = providers.adapter("claude", {"key": "k"})
        _request, _history, events = run_stream(adapter, broken)
        call = [p for k, p in events if k == "tool"][0]
        self.assertIsNone(call["input"])            # cut off: not run (tools.validate refuses None)
        self.assertIsNone(tools.validate("set_wifi", call["input"]))

    def test_openai(self):
        adapter = providers.adapter("openai", {"key": "sk-test", "model": "gpt-5.5"})
        request, history, events = run_stream(adapter, fake.openai_tool_turn())
        self.assertEqual(request["url"], "https://api.openai.com/v1/responses")
        headers = {k.lower(): v for k, v in request["headers"].items()}
        self.assertEqual(headers["authorization"], "Bearer sk-test")
        body = request["body"]
        self.assertEqual((body["store"], body["stream"], body["instructions"]), (False, True, "system"))
        self.assertEqual(body["input"], [{"role": "user", "content": "Turn on Wi-Fi"}])
        self.assertEqual(body["tools"][0]["type"], "function")
        self.assertEqual("".join(p for k, p in events if k == "text"), "Turning on Wi-Fi.")
        calls = [p for k, p in events if k == "tool"]
        self.assertEqual(calls, [{"id": "call_1", "name": "set_wifi", "input": {"on": True}}])
        # Reasoning item, message and call go back as they came.
        self.assertEqual([item["type"] for item in adapter.turn], ["reasoning", "message", "function_call"])
        history.extend(adapter.turn)
        adapter.add_tool_results(history, [(calls[0], '{"ok": true}', False)])
        self.assertEqual(history[-1], {"type": "function_call_output", "call_id": "call_1", "output": '{"ok": true}'})

    def test_copilot_is_azure_openai(self):
        adapter = providers.adapter("copilot", {"key": "az", "model": "my-gpt", "endpoint": "contoso.openai.azure.com/"})
        request = adapter.request([], "s", [])
        self.assertEqual(request.full_url, "https://contoso.openai.azure.com/openai/v1/responses")
        self.assertEqual(request.get_header("Api-key"), "az")
        self.assertEqual(json.loads(request.data)["model"], "my-gpt")
        self.assertIsNone(adapter.models_request())

    def test_gemini(self):
        adapter = providers.adapter("gemini", {"key": "AIza-test", "model": "gemini-flash-latest"})
        request, history, events = run_stream(adapter, fake.gemini_tool_turn())
        self.assertEqual(request["url"], "https://generativelanguage.googleapis.com/v1beta/models/"
                                         "gemini-flash-latest:streamGenerateContent?alt=sse")
        headers = {k.lower(): v for k, v in request["headers"].items()}
        self.assertEqual(headers["x-goog-api-key"], "AIza-test")
        body = request["body"]
        self.assertEqual(body["systemInstruction"], {"parts": [{"text": "system"}]})
        declarations = body["tools"][0]["functionDeclarations"]
        self.assertIn("parameters", declarations[0])          # set_wifi
        self.assertNotIn("parameters", declarations[1])       # no parameters: left out
        self.assertEqual("".join(p for k, p in events if k == "text"), "Turning on Wi-Fi.")
        calls = [p for k, p in events if k == "tool"]
        self.assertEqual((calls[0]["name"], calls[0]["input"]), ("set_wifi", {"on": True}))
        # Text joined, the call kept with its thought signature.
        self.assertEqual(adapter.turn, [{"role": "model", "parts": [
            {"text": "Turning on Wi-Fi."},
            {"functionCall": {"name": "set_wifi", "args": {"on": True}}, "thoughtSignature": "sig-g"}]}])
        history.extend(adapter.turn)
        adapter.add_tool_results(history, [(calls[0], '{"ok": true}', False)])
        self.assertEqual(history[-1], {"role": "user", "parts": [
            {"functionResponse": {"name": "set_wifi", "response": {"result": '{"ok": true}'}}}]})

    def test_errors_and_models(self):
        adapter = providers.adapter("openai", {"key": "bad"})
        with self.assertRaises(providers.ServiceError) as caught:
            list(providers.stream(adapter, [], "s", [], fake.FakeService(401)))
        self.assertEqual(caught.exception.kind, "key")
        with self.assertRaises(providers.ServiceError) as caught:
            list(providers.stream(adapter, [], "s", [], fake.FakeService(urllib.error.URLError("no route"))))
        self.assertEqual(caught.exception.kind, "network")
        self.assertEqual(providers.classify(429, "{}").kind, "rate")
        self.assertEqual(providers.classify(404, '{"error": {"message": "model x not found"}}').kind, "model")
        listing = json.dumps({"data": [{"id": "gpt-5.5"}, {"id": "text-embedding-3"}, {"id": "gpt-6-sol"},
                                       {"id": "whisper-1"}, {"id": "o4-mini"}]}).encode()
        self.assertEqual(providers.list_models(adapter, fake.FakeService(listing)), ["o4-mini", "gpt-6-sol", "gpt-5.5"])
        gemini = providers.adapter("gemini", {"key": "k"})
        listing = json.dumps({"models": [
            {"name": "models/gemini-3.8-flash", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/text-embedding-004", "supportedGenerationMethods": ["embedContent"]}]}).encode()
        self.assertEqual(providers.list_models(gemini, fake.FakeService(listing)), ["gemini-3.8-flash"])
        self.assertEqual(providers.pick_model("openai", ["gpt-5.5", "gpt-6-sol"]), "gpt-6-sol")
        self.assertEqual(providers.pick_model("openai", ["gpt-5.5", "gpt-6-sol"], "gpt-5.5"), "gpt-5.5")


class ToolTests(unittest.TestCase):
    def test_validate(self):
        self.assertEqual(tools.validate("set_volume", {"percent": 40}), {"percent": 40})
        self.assertEqual(tools.validate("set_volume", {"percent": 40.0}), {"percent": 40})
        self.assertIsNone(tools.validate("set_volume", {"percent": "40"}))
        self.assertIsNone(tools.validate("set_volume", {}))
        self.assertIsNone(tools.validate("set_theme", {"mode": "purple"}))
        self.assertIsNone(tools.validate("rm_rf", {}))
        self.assertEqual(tools.validate("set_wifi", {"on": False, "extra": 1}), {"on": False})
        self.assertIsNone(tools.validate("set_wifi", {"on": "yes"}))
        self.assertFalse(tools.needs_approval("get_system_info"))
        self.assertTrue(tools.needs_approval("set_theme"))
        for tool in tools.TOOLS:
            self.assertEqual(tool["parameters"]["type"], "object")
            self.assertTrue(tool["description"])

    def test_titles_in_both_languages(self):
        self.assertEqual(tools.title("set_theme", {"mode": "dark"}, "tr"), "Koyu moda geç")
        self.assertEqual(tools.title("set_volume", {"percent": 30}, "en"), "Set the volume to 30%")
        self.assertEqual(tools.title("open_folder", {"folder": "downloads"}, "tr"),
                         "İndirilenler klasörünü Dosya Gezgini'nde aç")
        for tool in tools.TOOLS:
            for lang in ("en", "tr"):
                self.assertNotEqual(tools.title(tool["name"], {}, lang), tool["name"])
        for key, pair in strings.TEXTS.items():
            self.assertTrue(pair[0] and pair[1], key)

    def test_execute(self):
        started, ran = [], []

        def runner(command, timeout=30):
            ran.append(command)
            return 0, ""
        ok, output = tools.execute("open_url", {"url": "file:///etc/passwd"}, "en", started.append, runner)
        self.assertFalse(ok)
        ok, output = tools.execute("open_url", {"url": "https://example.com/a"}, "en", started.append, runner)
        self.assertTrue(ok)
        self.assertEqual(started[-1], ["xdg-open", "https://example.com/a"])
        home = Path(tempfile.mkdtemp())
        (home / "Belgeler").mkdir()
        os.environ["HOME"] = str(home)
        ok, _ = tools.execute("open_folder", {"folder": "home", "path": "/etc"}, "en", started.append, runner)
        self.assertFalse(ok)                                   # outside the home folder
        ok, _ = tools.execute("open_folder", {"folder": "home", "path": "Belgeler"}, "en", started.append, runner)
        self.assertTrue(ok)
        self.assertEqual(started[-1], ["veltos-explorer", str((home / "Belgeler").resolve())])
        ok, _ = tools.execute("open_folder", {"folder": "this_pc"}, "en", started.append, runner)
        self.assertEqual(started[-1], ["veltos-explorer", "thispc:"])
        ok, _ = tools.execute("set_do_not_disturb", {"on": True}, "en", started.append, runner)
        self.assertEqual(ran[-1][-1], "2999,12,31,0,0,0")
        # Settings' own helpers do the switching (a stand-in here).
        calls = []

        class Helper:
            def __init__(self, run):
                pass

            def set_wifi(self, on):
                calls.append(("wifi", on))
                return True

            def set_powered(self, on):
                calls.append(("bt", on))
                return True

            def set_muted(self, kind, muted):
                calls.append(("mute", kind, muted))
                return True

            def set_volume(self, kind, percent):
                calls.append(("volume", kind, percent))
                return True
        old = tools.settings_helpers
        tools.settings_helpers = lambda: SimpleNamespace(Network=Helper, Bluetooth=Helper, Sound=Helper)
        try:
            self.assertTrue(tools.execute("set_wifi", {"on": True}, "en", started.append, runner)[0])
            self.assertTrue(tools.execute("set_bluetooth", {"on": False}, "en", started.append, runner)[0])
            self.assertTrue(tools.execute("set_volume", {"percent": 150}, "en", started.append, runner)[0])
        finally:
            tools.settings_helpers = old
        self.assertEqual(calls, [("wifi", True), ("bt", False), ("mute", "sink", False), ("volume", "sink", 150)])

    def test_find_app_and_search(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "veltos-calculator.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=Calculator\nName[tr]=Hesap Makinesi\nExec=x\n", encoding="utf-8")
        (folder / "hidden.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=Calculator helper\nNoDisplay=true\n", encoding="utf-8")
        self.assertEqual(tools.find_app("hesap makinesi", "tr", [folder])[1], "Hesap Makinesi")
        self.assertEqual(tools.find_app("calc", "en", [folder])[0].name, "veltos-calculator.desktop")
        self.assertIsNone(tools.find_app("photoshop", "en", [folder]))
        root = Path(tempfile.mkdtemp())
        (root / "Belgeler").mkdir()
        (root / "Belgeler" / "Rapor 2026.docx").write_text("x")
        (root / ".gizli").mkdir()
        (root / ".gizli" / "rapor.txt").write_text("x")
        self.assertEqual(tools.search_files("rapor", root=root), [str(root / "Belgeler" / "Rapor 2026.docx")])
        info = tools.system_info()
        self.assertIn("cores", info)


class ConfigTests(unittest.TestCase):
    def test_saved_for_the_user_only(self):
        file = Path(tempfile.mkdtemp()) / "veltos" / "ai.json"
        data = config.load(file)
        self.assertFalse(config.ready(data))
        data["provider"] = "claude"
        data["services"]["claude"]["key"] = "sk-ant-x"
        config.save(data, file)
        self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600)
        again = config.load(file)
        self.assertTrue(config.ready(again))
        self.assertEqual(again["services"]["claude"]["model"], "claude-opus-5-5")
        again["provider"] = "copilot"
        again["services"]["copilot"]["key"] = "az"
        self.assertFalse(config.ready(again))                 # no endpoint and deployment yet


class BackendTests(unittest.TestCase):
    def setUp(self):
        from PySide6.QtGui import QGuiApplication
        self.app = QGuiApplication.instance() or QGuiApplication([])
        self.file = Path(tempfile.mkdtemp()) / "ai.json"

    def backend(self, provider, *answers, actions=True):
        from veltos_ai import app
        data = config.load(self.file)
        data["provider"] = provider
        data["services"][provider]["key"] = "test-key"
        data["actions"] = actions
        config.save(data, self.file)
        self.service = fake.FakeService(*answers)
        self.ran = []
        return app.Backend(lang="en", opener=self.service, settings_file=self.file, threaded=False,
                           starter=lambda command: self.ran.append(command))

    def test_local_model_named_in_the_session_language(self):
        # The service list showed "Local model (free, offline)" in Turkish (2026-10-31).
        backend = self.backend("local")
        backend.lang = "tr"
        titles = {s["id"]: s["title"] for s in backend.services}
        self.assertEqual(titles["local"], "Yerel model (ücretsiz, çevrimdışı)")
        self.assertEqual(titles["claude"], "Claude (Anthropic)")
        self.assertTrue(backend.providerTitle.startswith("Yerel model"))

    def stub_wifi(self):
        old = tools.settings_helpers
        done = []

        class Network:
            def __init__(self, run):
                pass

            def set_wifi(self, on):
                done.append(on)
                return True
        tools.settings_helpers = lambda: SimpleNamespace(Network=Network)
        self.addCleanup(setattr, tools, "settings_helpers", old)
        return done

    def test_local_command_without_the_model(self):
        # "Wi-Fi'ı aç" with the local model: the command becomes its action
        # at once (intents.py); when the model then cannot start, the answer
        # is "Done." instead of an error, as the command did its work.
        from veltos_ai import local
        old_home = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp()
        self.addCleanup(lambda: os.environ.__setitem__("XDG_DATA_HOME", old_home) if old_home
                        else os.environ.pop("XDG_DATA_HOME", None))
        local.models_dir().mkdir(parents=True)
        (local.models_dir() / providers.PROVIDERS["local"]["model"]).write_bytes(b"x")

        def no_engine(_model):
            raise local.DownloadError("engine")
        self.addCleanup(setattr, local.SERVER_INSTANCE, "base", local.SERVER_INSTANCE.base)
        local.SERVER_INSTANCE.base = no_engine
        # The engine is installed but fails (veltos-llama is not in the build).
        self.addCleanup(setattr, local, "engine_available", local.engine_available)
        local.engine_available = lambda: True
        done = self.stub_wifi()
        backend = self.backend("local")
        backend.send("Wi-Fi'ı aç")
        messages = backend.messages
        self.assertEqual([m["kind"] for m in messages], ["user", "action"])
        self.assertEqual((messages[1]["title"], messages[1]["state"]), ("Turn on Wi-Fi", "ask"))
        self.assertEqual(self.service.requests, [])           # the model was not asked
        backend.allowAction(messages[1]["id"])
        self.assertEqual(done, [True])
        self.assertEqual((backend.messages[-1]["kind"], backend.messages[-1]["text"]), ("assistant", "Done."))
        self.assertFalse(backend.busy)

    def test_no_tools_after_a_recognised_command(self):
        # After "install sl" had worked, the local model went on to ask for
        # "install slack" (2026-10-31): its follow-up only words the answer.
        backend = self.backend("openai", fake.openai_text("Hello."), fake.openai_text("Done."))
        backend.send("Hello")
        self.assertIn("tools", self.service.requests[0]["body"])
        backend._command_done = True
        backend._start_turn()
        self.assertNotIn("tools", self.service.requests[1]["body"])

    def test_allow(self):
        for provider, first, second in (("claude", fake.claude_tool_turn(), fake.claude_text("Wi-Fi is on.")),
                                        ("openai", fake.openai_tool_turn(), fake.openai_text("Wi-Fi is on.")),
                                        ("gemini", fake.gemini_tool_turn(), fake.gemini_text("Wi-Fi is on."))):
            with self.subTest(provider=provider):
                done = self.stub_wifi()
                backend = self.backend(provider, first, second)
                backend.send("Turn on Wi-Fi")
                messages = backend.messages
                self.assertEqual([m["kind"] for m in messages], ["user", "assistant", "action"])
                self.assertEqual(messages[1]["text"], "Turning on Wi-Fi.")
                self.assertEqual((messages[2]["title"], messages[2]["state"]), ("Turn on Wi-Fi", "ask"))
                self.assertTrue(backend.busy)
                self.assertEqual(done, [])                    # nothing happens before "Allow"
                backend.allowAction(messages[2]["id"])
                self.assertEqual(done, [True])
                messages = backend.messages
                self.assertEqual(messages[2]["state"], "done")
                self.assertEqual(messages[-1]["text"], "Wi-Fi is on.")
                self.assertFalse(backend.busy)
                self.assertEqual(len(self.service.requests), 2)

    def test_deny_and_stop(self):
        done = self.stub_wifi()
        backend = self.backend("claude", fake.claude_tool_turn(), fake.claude_text("Okay, I left it."))
        backend.send("Turn on Wi-Fi")
        backend.denyAction(backend.messages[2]["id"])
        self.assertEqual(done, [])
        self.assertEqual(backend.messages[2]["state"], "denied")
        result = self.service.requests[1]["body"]["messages"][-1]["content"][0]
        self.assertEqual((result["type"], result["is_error"]), ("tool_result", True))
        # Stopping while an action waits: the call still gets a result.
        backend = self.backend("claude", fake.claude_tool_turn())
        backend.send("Turn on Wi-Fi")
        backend.stop()
        self.assertFalse(backend.busy)
        self.assertEqual(backend.history[-1]["content"][0]["type"], "tool_result")

    def test_actions_off_errors_and_new_chat(self):
        backend = self.backend("claude", fake.claude_tool_turn(), fake.claude_text("Actions are off."), actions=False)
        backend.send("Turn on Wi-Fi")
        self.assertEqual(backend.messages[2]["state"], "denied")
        self.assertEqual([t["name"] for t in self.service.requests[0]["body"]["tools"]],
                         ["get_system_info", "search_files", "list_wifi_networks"])
        backend = self.backend("openai", 401)
        backend.send("hello")
        self.assertEqual(backend.messages[-1]["kind"], "error")
        self.assertEqual(backend.messages[-1]["text"], strings.text("en", "error_key"))
        backend.newChat()
        self.assertEqual(backend.messages, [])
        backend = self.backend("claude", fake.claude_text("No.", stop="refusal"))
        backend.send("x")
        self.assertEqual(backend.messages[-1]["text"], strings.text("en", "refused"))

    def test_conversation_kept_between_starts(self):
        # A closed pane's process ends after ten idle minutes; the next start
        # knew nothing of the conversation (product owner, 2026-10-31).
        from veltos_ai import app, conversation
        kept = Path(tempfile.mkdtemp()) / "veltos-ai" / "conversation.json"
        backend = self.backend("claude", fake.claude_text("Hi Ayşe."))
        backend._conversation_file = kept
        backend.send("My name is Ayşe.")
        backend.save_conversation()
        self.assertEqual(stat.S_IMODE(kept.stat().st_mode), 0o600)
        service = fake.FakeService(fake.claude_text("Your name is Ayşe."))
        again = app.Backend(lang="en", opener=service, settings_file=self.file, threaded=False,
                            conversation_file=kept)
        self.assertEqual([m["text"] for m in again.messages], ["My name is Ayşe.", "Hi Ayşe."])
        self.assertEqual(again.chat.count, 2)
        again.send("What is my name?")
        sent = service.requests[0]["body"]["messages"]
        self.assertEqual([m["role"] for m in sent], ["user", "assistant", "user"])
        self.assertEqual(sent[0]["content"], "My name is Ayşe.")
        again.newChat()
        self.assertFalse(kept.exists())
        # An action still waiting when the panel ended was not run.
        kept.write_text(json.dumps({"messages": [
            {"id": 1, "kind": "user", "text": "Turn on Wi-Fi"},
            {"id": 2, "kind": "action", "title": "Turn on Wi-Fi", "state": "ask"},
            {"id": 3, "kind": "assistant", "text": "Turn", "state": "streaming"},
            {"id": "x", "kind": "user"}], "history": [], "provider": "claude"}), encoding="utf-8")
        state = conversation.load(kept)
        self.assertEqual([(m["id"], m["state"]) for m in state["messages"]], [(1, ""), (2, "denied"), (3, "stopped")])
        kept.write_text("not json", encoding="utf-8")
        self.assertEqual(conversation.load(kept), {"messages": [], "history": [], "provider": ""})

    def test_another_service_hears_the_conversation(self):
        # A conversation kept from another service (chosen in VeltOS Settings
        # while the panel was closed): the history was emptied and the new
        # service knew nothing of what the panel still showed.
        from veltos_ai import app, conversation
        kept = Path(tempfile.mkdtemp()) / "conversation.json"
        conversation.save(kept, [{"id": 1, "kind": "user", "text": "My name is Ayşe."},
                                 {"id": 2, "kind": "assistant", "text": "Hi Ayşe.", "state": ""},
                                 {"id": 3, "kind": "action", "title": "Turn on Wi-Fi", "state": "done"}],
                          [{"role": "user", "content": "My name is Ayşe."}], "claude")
        self.backend("gemini")
        service = fake.FakeService(fake.gemini_text("Ayşe."))
        backend = app.Backend(lang="en", opener=service, settings_file=self.file, threaded=False,
                              conversation_file=kept)
        backend.send("What is my name?")
        contents = service.requests[0]["body"]["contents"]
        self.assertEqual(contents, [{"role": "user", "parts": [{"text": "My name is Ayşe."}]},
                                    {"role": "model", "parts": [{"text": "Hi Ayşe."}]},
                                    {"role": "user", "parts": [{"text": "What is my name?"}]}])

    def test_stopped_answer_stays_in_the_history(self):
        backend = self.backend("claude")
        backend._adapter = providers.adapter("claude", {"key": "k"})
        backend._current = backend._add("assistant", "", state="streaming")
        backend._set_busy(True)
        backend._on_event(backend._generation, "text", "The first part")
        backend._cancel.set()
        backend._on_event(backend._generation, "finished", None)
        self.assertEqual(backend.messages[-1]["state"], "stopped")
        self.assertEqual(backend.history[-1], {"role": "assistant", "content": "The first part"})

    def test_chat_rows_change_in_place(self):
        # The view's list was made again for every streamed piece and jumped.
        from veltos_ai import app
        model = app.ChatModel()
        events = []
        model.rowsInserted.connect(lambda _parent, first, _last: events.append(("insert", first)))
        model.rowsRemoved.connect(lambda _parent, first, _last: events.append(("remove", first)))
        model.dataChanged.connect(lambda first, _last, _roles=None: events.append(("change", first.row())))
        model.modelReset.connect(lambda: events.append(("reset",)))
        messages = [{"id": 1, "kind": "user", "text": "hi"}, {"id": 2, "kind": "assistant", "state": "streaming"}]
        model.sync(messages)
        messages[1]["text"] = "Hel"
        model.sync(messages)
        model.sync(messages)                 # nothing changed: no signal
        messages.pop(1)
        model.sync(messages)
        self.assertEqual(events, [("insert", 0), ("insert", 1), ("change", 1), ("remove", 1)])
        self.assertEqual(model.count, 1)
        model.sync([{"id": 5, "kind": "user", "text": "b"}, {"id": 1, "kind": "user", "text": "hi"}])
        self.assertEqual(events[-1], ("insert", 0))
        model.sync([{"id": 1, "kind": "user", "text": "hi"}, {"id": 5, "kind": "user", "text": "b"}])
        self.assertEqual(events[-1], ("reset",))           # never happens: shown anew
        self.assertEqual([r["mid"] for r in model.rows], [1, 5])

    def test_follows_the_theme(self):
        # The pane can switch the theme itself; its colours follow at once.
        home = Path(tempfile.mkdtemp())
        old = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(home)
        try:
            (home / "kdeglobals").write_text("[KDE]\nLookAndFeelPackage=org.veltos.dark\n", encoding="utf-8")
            backend = self.backend("claude")
            self.assertTrue(backend.darkMode)
            changes = []
            backend.lookChanged.connect(lambda: changes.append(backend.darkMode))
            (home / "kdeglobals").write_text("[KDE]\nLookAndFeelPackage=org.veltos.light\n[General]\n"
                                             "AccentColor=232,17,35\n", encoding="utf-8")
            backend._reload_look()
            self.assertEqual(changes, [False])
            self.assertEqual(backend.accent, "#e81123")
            backend._reload_look()                     # nothing changed: no signal
            self.assertEqual(changes, [False])
        finally:
            if old is None:
                os.environ.pop("XDG_CONFIG_HOME", None)
            else:
                os.environ["XDG_CONFIG_HOME"] = old

    def test_settings(self):
        backend = self.backend("claude")
        backend.saveService("gemini", "AIza", "", "")
        self.assertEqual(backend.provider, "gemini")
        self.assertEqual(backend.providerTitle, "Gemini · gemini-flash-latest")
        saved = json.loads(self.file.read_text(encoding="utf-8"))
        self.assertEqual(saved["services"]["gemini"]["key"], "AIza")
        backend.saveService("gemini", "", "gemini-3.8-flash", "")
        self.assertEqual(json.loads(self.file.read_text(encoding="utf-8"))["services"]["gemini"]["key"], "AIza")
        backend.removeKey("gemini")
        self.assertFalse(backend.ready)


if __name__ == "__main__":
    unittest.main()
