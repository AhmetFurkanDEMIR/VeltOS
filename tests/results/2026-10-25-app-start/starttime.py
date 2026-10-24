#!/usr/bin/python3
# Dev aid (VM): how long a VeltOS app takes from start to its first drawn
# frame. Runs the app's launcher with QQmlApplicationEngine.load patched to
# report the first frameSwapped of the window, then quits.
#   starttime.py /usr/bin/veltos-calculator [args...]
import os
import sys
import time

START = time.monotonic()
from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

original = QQmlApplicationEngine.load
seen = {"done": False}


def load(self, *args):
    t0 = time.monotonic()
    result = original(self, *args)
    loaded = time.monotonic()
    roots = self.rootObjects()
    if roots and hasattr(roots[0], "frameSwapped"):
        def swapped():
            if not seen["done"]:
                seen["done"] = True
                now = time.monotonic()
                print(f"STARTUP {os.path.basename(sys.argv[0])}: first frame {now - START:.2f} s "
                      f"(QML load {loaded - t0:.2f} s, before load {t0 - START:.2f} s)", flush=True)
                QTimer.singleShot(200, QGuiApplication.quit)
        roots[0].frameSwapped.connect(swapped)
    return result


QQmlApplicationEngine.load = load
script = sys.argv[1]
sys.argv = sys.argv[1:]
code = compile(open(script, encoding="utf-8").read(), script, "exec")
try:
    exec(code, {"__name__": "__main__", "__file__": script})
except SystemExit:
    pass
os._exit(0)
