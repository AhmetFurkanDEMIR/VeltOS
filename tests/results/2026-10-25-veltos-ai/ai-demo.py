"""Dev VM demo of VeltOS AI with a stand-in service (no API key here):
the real pane and the real actions, the answers recorded in Claude's
stream format. Not shipped."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/tmp/aitest")
import fakeservice as fake  # noqa: E402
from PySide6.QtCore import QTimer, QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from veltos_ai import app as aiapp, config  # noqa: E402


def turn(text, tool=None, stop="end_turn"):
    events = [("content_block_start", {"type": "content_block_start", "index": 0,
                                       "content_block": {"type": "text", "text": ""}}),
              ("content_block_delta", {"type": "content_block_delta", "index": 0,
                                       "delta": {"type": "text_delta", "text": text}}),
              ("content_block_stop", {"type": "content_block_stop", "index": 0})]
    if tool:
        events += [("content_block_start", {"type": "content_block_start", "index": 1,
                                            "content_block": {"type": "tool_use", "id": "toolu_d", "name": tool[0],
                                                              "input": {}}}),
                   ("content_block_delta", {"type": "content_block_delta", "index": 1,
                                            "delta": {"type": "input_json_delta", "partial_json": json.dumps(tool[1])}}),
                   ("content_block_stop", {"type": "content_block_stop", "index": 1})]
        stop = "tool_use"
    events += [("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop}}),
               ("message_stop", {"type": "message_stop"})]
    return fake.sse(events)


ANSWER = ("İşte bu bilgisayarın özeti:\n\n- **İşletim sistemi:** VeltOS\n- **Bellek:** 8 GB\n"
          "- **Disk:** boş alan bol\n\nBaşka bir şey ister misiniz?")


def main():
    app = QGuiApplication(sys.argv)
    try:
        from veltos_controls import use
        use()
    except ImportError:
        pass
    file = Path(tempfile.mkdtemp()) / "ai.json"
    data = config.load(file)
    data["provider"] = "claude"
    data["services"]["claude"]["key"] = "demo-key"
    config.save(data, file)
    service = fake.FakeService(
        turn("Bu bilgisayarın ayrıntılarına bakıyorum.", ("get_system_info", {})), turn(ANSWER),
        turn("Koyu moda geçiyorum.", ("set_theme", {"mode": "dark"})),
        turn("Koyu moda geçildi. Açık moda dönmek isterseniz söylemeniz yeterli."))
    backend = aiapp.Backend(lang="tr", opener=service, settings_file=file)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(aiapp.QML_DIR / "Main.qml")))
    window = engine.rootObjects()[0]
    window.show()
    script = sys.argv[1] if len(sys.argv) > 1 else ""
    if "info" in script:
        QTimer.singleShot(2500, lambda: backend.send("Bu bilgisayarda neler var?"))
    if "theme" in script:
        QTimer.singleShot(6000, lambda: backend.send("Koyu moda geç"))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
