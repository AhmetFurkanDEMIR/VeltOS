"""python3 -m veltos_notepad (used for "New window")."""
import os
import sys

os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop")
os.environ["QML_DISABLE_DISK_CACHE"] = "1"

from veltos_notepad.app import main  # noqa: E402

sys.exit(main())
