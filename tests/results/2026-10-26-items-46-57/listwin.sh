#!/bin/sh
# Dev aid: print every window's caption, class and process id through a
# KWin script (output in the user journal). Run inside the Plasma session
# (vsess.py).
cat > /tmp/listwin.js <<'EOF'
workspace.windowList().forEach(function (w) {
    var g = w.frameGeometry;
    print("VELTOSWIN|" + w.caption + "|" + w.resourceClass + "|" + w.pid + "|" + g.x + "," + g.y + " " + g.width + "x" + g.height + "|min=" + w.minimized + "|skipTaskbar=" + w.skipTaskbar + "|transient=" + w.transient + "|type=" + w.windowType + "|desktopFile=" + w.desktopFileName);
});
EOF
id=$(qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript /tmp/listwin.js veltos-listwin)
qdbus6 org.kde.KWin /Scripting/Script$id org.kde.kwin.Script.run
sleep 1
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript veltos-listwin >/dev/null
journalctl --user -b --since "-20s" -o cat | grep VELTOSWIN | sort -u
