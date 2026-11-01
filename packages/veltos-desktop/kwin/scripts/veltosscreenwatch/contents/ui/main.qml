/*
    VeltOS screen watch: the taskbar comes back after a screen goes away.

    The product owner's laptop lost its taskbar for good when the HDMI
    monitor that had been made display 1 was unplugged (2026-11-01). The
    dev VM's virtual screens always got it back, and Plasma has a long
    line of such bugs (bugs.kde.org 347195, 485313, 499383) whose remedy is
    starting plasmashell again. Windows always shows its taskbar, so this
    script looks at what the user sees: a few seconds after the screens
    changed, is one of Plasma's panel windows on a screen? If it still is
    not a few seconds later, plasmashell is restarted through systemd
    (plasma-plasmashell.service), at most once a minute.

    Only after a panel has been seen in this session: while Plasma starts
    there is no panel yet, and that is no reason to restart it.

    Uses KWin's public QML API (org.kde.kwin) only.
    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import org.kde.kwin as KWin

Item {
    id: watch

    // A panel window was seen in this session.
    property bool seenPanel: false
    // When plasmashell was last restarted (ms since the epoch).
    property real lastRestart: 0
    readonly property int minimumGap: 60000

    function isPanel(w) {
        return !!w && w.dock && w.resourceClass === "plasmashell";
    }

    function overlaps(a, b) {
        return a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;
    }

    function panelShown() {
        const screens = KWin.Workspace.screens || [];
        const order = KWin.Workspace.stackingOrder;
        for (let i = 0; i < order.length; i++) {
            const w = order[i];
            if (!watch.isPanel(w) || w.minimized)
                continue;
            watch.seenPanel = true;
            for (let j = 0; j < screens.length; j++) {
                if (watch.overlaps(w.frameGeometry, screens[j].geometry))
                    return true;
            }
        }
        return false;
    }

    Component.onCompleted: watch.panelShown()

    Connections {
        target: KWin.Workspace
        function onScreensChanged() {
            confirm.stop();
            settle.restart();
        }
        function onWindowAdded(w) {
            if (watch.isPanel(w))
                watch.seenPanel = true;
        }
    }

    // Plasma moves its panels itself once the screens settle.
    Timer {
        id: settle
        interval: 4000
        onTriggered: {
            if (watch.seenPanel && !watch.panelShown())
                confirm.restart();
        }
    }
    Timer {
        id: confirm
        interval: 4000
        onTriggered: {
            if (watch.panelShown() || Date.now() - watch.lastRestart < watch.minimumGap)
                return;
            watch.lastRestart = Date.now();
            console.info("veltosscreenwatch: no taskbar on any screen, restarting plasmashell");
            restart.call();
        }
    }

    KWin.DBusCall {
        id: restart
        service: "org.freedesktop.systemd1"
        path: "/org/freedesktop/systemd1"
        dbusInterface: "org.freedesktop.systemd1.Manager"
        method: "RestartUnit"
        arguments: ["plasma-plasmashell.service", "replace"]
    }
}
