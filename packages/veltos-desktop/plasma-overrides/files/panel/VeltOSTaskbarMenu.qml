/*
    VeltOS: Windows 11's taskbar menu. Right-clicking the taskbar where
    nothing has a menu of its own (empty space, the gaps between buttons)
    offers Task Manager and Taskbar settings, as Windows 11 does; Plasma's
    containment menu ("Enter Edit Mode", "Add Widgets") never opens, the
    taskbar is locked. Added to Plasma's panel containment (org.kde.panel,
    plasma-desktop 6.3) by update-plasma-overrides; it lies under the
    applets, so their own menus (taskbar buttons, Start, tray icons, the
    clock) come first.

    Texts come from the veltos-desktop catalog (i18nd).

    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as Plasma5Support

MouseArea {
    id: area

    readonly property string domain: "veltos-desktop"
    function tr(text) {
        return i18nd(domain, text);
    }

    acceptedButtons: Qt.RightButton
    onPressed: mouse => {
        menu.visualParent = area;
        menu.open(Math.round(mouse.x), Math.round(mouse.y));
    }

    Plasma5Support.DataSource {
        id: shell
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }

    PlasmaExtras.Menu {
        id: menu
        placement: PlasmaExtras.Menu.TopPosedLeftAlignedPopup

        PlasmaExtras.MenuItem {
            text: area.tr("Task Manager")
            icon: "veltos-taskmanager"
            onClicked: shell.connectSource("veltos-taskmanager")
        }
        PlasmaExtras.MenuItem { separator: true }
        PlasmaExtras.MenuItem {
            text: area.tr("Taskbar settings")
            icon: "configure"
            onClicked: shell.connectSource("veltos-settings taskbar")
        }
    }
}
