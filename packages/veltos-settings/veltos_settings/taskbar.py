"""Personalization > Taskbar: Windows 11's taskbar settings.

They live in Plasma's taskbar itself (the panel and its applets) and are
read and changed through plasmashell's scripting interface
(org.kde.PlasmaShell.evaluateScript), which also updates the running
taskbar at once. The taskbar is locked against editing (session-fixups);
scripts can still change it.

    search       0 hide, 1 search icon only, 2 search icon and label,
                 3 search box (org.veltos.search "mode")
    taskView     the Task View button (org.veltos.taskview "shown")
    alignment    "center" or "left": the spacer before Start grows or not
    autoHide     the taskbar hides until the pointer reaches it
    badges       counters on app buttons (task manager smartLaunchersEnabled)
    combine      "always", "full" (when the taskbar is full) or "never"
    showDesktop  the far corner shows the desktop (org.veltos.showdesktop)
    tray         {applet id: true} for the tray icons shown on the taskbar
                 rather than behind the "^" arrow

Commands go through `run` so tests can use a fake runner.
"""

import json

from .devices import run

TASKS = ("org.kde.plasma.icontasks", "org.kde.plasma.taskmanager")
# Tray icons that can sit on the taskbar or behind the arrow, with their
# Windows 11 names (Settings lists them under "Other system tray icons").
TRAY_ITEMS = [
    ("org.kde.plasma.devicenotifier", ("Safely Remove Hardware and Eject Media", "Donanımı Güvenle Kaldır ve Medyayı Çıkar"),
     "media-removable-symbolic"),
    ("org.kde.plasma.keyboardlayout", ("Input indicator", "Giriş göstergesi"), "input-keyboard-symbolic"),
    ("org.kde.plasma.mediacontroller", ("Media playback", "Medya oynatma"), "media-playback-start-symbolic"),
    ("org.kde.plasma.clipboard", ("Clipboard", "Pano"), "edit-paste-symbolic"),
    ("org.kde.plasma.printmanager", ("Printers", "Yazıcılar"), "printer-symbolic"),
]
SEARCH_MODES = (0, 1, 2, 3)
ALIGNMENTS = ("center", "left")
COMBINE = ("always", "full", "never")
DEFAULTS = {"search": 3, "taskView": True, "alignment": "center", "autoHide": False, "badges": True,
            "combine": "full", "showDesktop": True,
            "tray": {"org.kde.plasma.keyboardlayout": True}}

# Shared by every script: the taskbar is the panel with the task manager.
PRELUDE = """
var TASKS = %s;
function taskbars() {
    return panels().filter(function (panel) {
        return TASKS.some(function (id) { return panel.widgets(id).length > 0; });
    });
}
function first(panel, id) {
    var list = panel.widgets(id);
    return list.length > 0 ? list[0] : null;
}
function tray(panel) {
    var widget = first(panel, 'org.kde.plasma.systemtray');
    var id = widget ? widget.readConfig('SystrayContainmentId') : null;
    return id ? desktopById(id) : null;
}
function list(value) {
    if (typeof value === 'string') {
        return value ? value.split(',') : [];
    }
    return value || [];
}
// The spacer before Start (layout.js adds it first): it centres the
// taskbar's buttons while it grows.
function leadingSpacer(panel) {
    var start = first(panel, 'org.veltos.startmenu');
    var spacers = panel.widgets('org.kde.plasma.panelspacer').filter(function (spacer) {
        return !start || spacer.id < start.id;
    });
    spacers.sort(function (a, b) { return a.id - b.id; });
    return spacers.length > 0 ? spacers[0] : null;
}
""" % json.dumps(list(TASKS))

READ = PRELUDE + """
var state = {};
taskbars().slice(0, 1).forEach(function (panel) {
    state.autoHide = panel.hiding === 'autohide';
    var search = first(panel, 'org.veltos.search');
    if (search) {
        search.currentConfigGroup = ['General'];
        state.search = Number(search.readConfig('mode', 3));
    } else {
        state.search = 0;
    }
    var view = first(panel, 'org.veltos.taskview');
    if (view) {
        view.currentConfigGroup = ['General'];
        state.taskView = String(view.readConfig('shown', true)) !== 'false';
    } else {
        state.taskView = false;
    }
    var corner = first(panel, 'org.veltos.showdesktop');
    if (corner) {
        corner.currentConfigGroup = ['General'];
        state.showDesktop = String(corner.readConfig('enabled', true)) !== 'false';
    } else {
        state.showDesktop = false;
    }
    var spacer = leadingSpacer(panel);
    if (spacer) {
        spacer.currentConfigGroup = ['General'];
        state.alignment = String(spacer.readConfig('expanding', true)) === 'false' ? 'left' : 'center';
    }
    TASKS.forEach(function (id) {
        panel.widgets(id).forEach(function (tasks) {
            tasks.currentConfigGroup = ['General'];
            state.badges = String(tasks.readConfig('smartLaunchersEnabled', true)) !== 'false';
            var grouping = Number(tasks.readConfig('groupingStrategy', 1));
            var whenFull = String(tasks.readConfig('onlyGroupWhenFull', true)) !== 'false';
            state.combine = grouping === 0 ? 'never' : (whenFull ? 'full' : 'always');
        });
    });
    var t = tray(panel);
    if (t) {
        t.currentConfigGroup = ['General'];
        var shown = list(t.readConfig('shownItems', []));
        var hidden = list(t.readConfig('hiddenItems', []));
        state.tray = {};
        state.trayKnown = list(t.readConfig('extraItems', []));
        state.trayKnown.forEach(function (id) {
            state.tray[id] = shown.indexOf(id) >= 0 || hidden.indexOf(id) < 0;
        });
    }
});
print(JSON.stringify(state));
"""

# One change; %(value)s is a JSON literal.
WRITE = {
    "search": """
taskbars().forEach(function (panel) {
    panel.widgets('org.veltos.search').forEach(function (w) {
        w.currentConfigGroup = ['General'];
        w.writeConfig('mode', %(value)s);
    });
});""",
    "taskView": """
taskbars().forEach(function (panel) {
    panel.widgets('org.veltos.taskview').forEach(function (w) {
        w.currentConfigGroup = ['General'];
        w.writeConfig('shown', %(value)s);
    });
});""",
    "showDesktop": """
taskbars().forEach(function (panel) {
    panel.widgets('org.veltos.showdesktop').forEach(function (w) {
        w.currentConfigGroup = ['General'];
        w.writeConfig('enabled', %(value)s);
    });
});""",
    "alignment": """
taskbars().forEach(function (panel) {
    var spacer = leadingSpacer(panel);
    if (spacer) {
        spacer.currentConfigGroup = ['General'];
        spacer.writeConfig('expanding', %(value)s === 'center');
        if (%(value)s === 'left') {
            spacer.writeConfig('length', 1);
        }
    }
});""",
    "autoHide": """
taskbars().forEach(function (panel) {
    panel.hiding = %(value)s ? 'autohide' : 'none';
});""",
    "badges": """
taskbars().forEach(function (panel) {
    TASKS.forEach(function (id) {
        panel.widgets(id).forEach(function (w) {
            w.currentConfigGroup = ['General'];
            w.writeConfig('smartLaunchersEnabled', %(value)s);
        });
    });
});""",
    "combine": """
taskbars().forEach(function (panel) {
    TASKS.forEach(function (id) {
        panel.widgets(id).forEach(function (w) {
            w.currentConfigGroup = ['General'];
            w.writeConfig('groupingStrategy', %(value)s === 'never' ? 0 : 1);
            w.writeConfig('onlyGroupWhenFull', %(value)s === 'full');
        });
    });
});""",
}

TRAY_WRITE = """
taskbars().forEach(function (panel) {
    var t = tray(panel);
    if (!t) {
        return;
    }
    t.currentConfigGroup = ['General'];
    var id = %(id)s;
    var shown = list(t.readConfig('shownItems', [])).filter(function (x) { return x !== id; });
    var hidden = list(t.readConfig('hiddenItems', [])).filter(function (x) { return x !== id; });
    if (%(value)s) {
        shown.push(id);
    } else {
        hidden.push(id);
    }
    t.writeConfig('shownItems', shown);
    t.writeConfig('hiddenItems', hidden);
});"""


def evaluate_command(script):
    return ["qdbus6", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script]


def valid(name, value):
    """The value as the taskbar takes it, or None when it is not one."""
    if name == "search":
        return value if isinstance(value, int) and not isinstance(value, bool) and value in SEARCH_MODES else None
    if name == "alignment":
        return value if value in ALIGNMENTS else None
    if name == "combine":
        return value if value in COMBINE else None
    if name in ("taskView", "autoHide", "badges", "showDesktop"):
        return value if isinstance(value, bool) else None
    return None


class Taskbar:
    def __init__(self, runner=run):
        self.run = runner

    def state(self, lang="en"):
        code, out = self.run(evaluate_command(READ))
        state = dict(DEFAULTS, tray=dict(DEFAULTS["tray"]))
        available, known = False, None
        if code == 0:
            for line in reversed(out.strip().splitlines()):
                try:
                    found = json.loads(line)
                except ValueError:
                    continue
                if isinstance(found, dict):
                    available = bool(found)
                    known = found.pop("trayKnown", None)
                    tray = found.pop("tray", None)
                    if isinstance(tray, dict):
                        state["tray"] = {str(k): bool(v) for k, v in tray.items()}
                    state.update({k: v for k, v in found.items() if valid(k, v) is not None})
                    break
        index = 0 if lang != "tr" else 1
        state["trayItems"] = [{"id": item_id, "title": titles[index], "icon": icon,
                               "shown": bool(state["tray"].get(item_id, False))}
                              for item_id, titles, icon in TRAY_ITEMS
                              if not isinstance(known, list) or item_id in known]
        state["available"] = available
        return state

    def set(self, name, value):
        value = valid(name, value)
        if value is None:
            return False
        script = PRELUDE + WRITE[name] % {"value": json.dumps(value)}
        return self.run(evaluate_command(script))[0] == 0

    def set_tray_item(self, item_id, shown):
        if item_id not in {item[0] for item in TRAY_ITEMS} or not isinstance(shown, bool):
            return False
        script = PRELUDE + TRAY_WRITE % {"id": json.dumps(item_id), "value": json.dumps(shown)}
        return self.run(evaluate_command(script))[0] == 0
