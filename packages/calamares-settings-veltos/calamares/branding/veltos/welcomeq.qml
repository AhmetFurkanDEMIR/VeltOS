/*
    VeltOS installer: first page (Calamares module welcomeq).

    Calamares compiles a page's QML before it shows it, and meanwhile draws
    its own old-style "Loading…" spinner at the left of the page (product
    owner, 2026-10-23: "centre it, a Windows 11 icon and animation"). The
    style sheet hides that spinner, and this file is small enough to be
    ready at once: it shows Windows 11's progress ring in the middle of the
    page while the page itself (WelcomePage.qml) loads in the background,
    then fades the page in.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick

import "VeltTheme.js" as Theme

Rectangle {
    id: root

    color: Theme.c.window

    VeltSpinner {
        id: spinner
        objectName: "loadingRing"
        anchors.centerIn: parent
        width: 40
        height: 40
        opacity: welcome.status === Loader.Ready ? 0 : 1
        visible: opacity > 0
        running: visible
        Behavior on opacity { NumberAnimation { duration: 200 } }
    }

    Loader {
        id: welcome
        objectName: "welcomePage"
        anchors.fill: parent
        asynchronous: true
        source: "WelcomePage.qml"
        opacity: status === Loader.Ready ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 320; easing.type: Easing.OutCubic } }
    }
}
