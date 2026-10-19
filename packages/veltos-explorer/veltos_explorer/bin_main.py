"""Start-up shared by /usr/bin/veltos-explorer and `python3 -m veltos_explorer`."""

import os
import sys


def run():
    # The Plasma style for the few standard Qt Quick controls used (scroll
    # bars, pop-ups); it also lets Kirigami load icons from the icon theme.
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop")
    # Package builds give every file the same time stamp (SOURCE_DATE_EPOCH), so
    # Qt's QML disk cache would keep using the compiled QML of an older version
    # after an update; mixing old and new types crashed File Explorer (VM test,
    # 2026-10-19). Compile the QML at start instead.
    os.environ["QML_DISABLE_DISK_CACHE"] = "1"
    from veltos_explorer.app import main
    return main(sys.argv)
