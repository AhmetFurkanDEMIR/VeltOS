/*
    VeltOS taskbar previews: the window previews Windows 11 shows above a
    taskbar button.

    Pointing at the button of a running app shows, after a moment, one card
    per window of that app on the current desktop: the app's icon, the
    window title, a close button while the card is pointed at and a live
    picture of the window. A click on a card switches to its window; the
    close button or a middle click closes the window. Pointing at a card
    for a while shows that window alone, the others fade out (Peek).
    Moving to another button changes the cards at once; clicking a button,
    opening its menu or leaving the button and the cards hides them. When
    the cards would not fit on the screen they become a list, as on
    Windows.

    Plasma's own taskbar tooltips capture windows through the screen-cast
    service, which gives garbled pictures when KWin renders in software
    (virtual machines without 3D acceleration); KWin draws these pictures
    itself (WindowThumbnail), so they work with every renderer. Plasma's
    task manager tells KWin where the button of each window is (the target
    of the minimize animation, "iconGeometry"); an app's windows share
    their button, so the windows whose button contains the pointer are the
    pointed-at button's windows. The task manager's own window tooltips are
    off (plasma-overrides/org.kde.plasma.taskmanager.json).

    Uses KWin's public QML API (org.kde.kwin) only.
    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Window
import org.kde.kwin as KWin
import org.kde.kirigami as Kirigami

Window {
    id: preview

    // Sizes in logical pixels, like Windows 11 at 100 % scale (KWin scales
    // the window with its screen).
    readonly property int shadowMargin: 16
    readonly property int gap: 8
    readonly property int padding: 4
    readonly property int spacing: 4
    readonly property int cardPadding: 8
    readonly property int headerHeight: 32
    readonly property int maxThumbWidth: 224
    readonly property int minThumbWidth: 136
    readonly property int rowHeight: 40
    readonly property int listWidth: 320
    readonly property int screenMargin: 8

    // The pointed-at button (a global rectangle), its screen and windows.
    property rect button: Qt.rect(0, 0, 0, 0)
    property rect screenArea: Qt.rect(0, 0, 0, 0)
    property var windows: []
    // A button waiting to be shown.
    property var candidate: null
    // A button whose cards were closed by a click or a menu: they stay
    // closed until the pointer leaves it.
    property rect suppressed: Qt.rect(0, 0, 0, 0)
    property bool shown: false
    // Peek: the window shown alone and the opacity of the others.
    property QtObject peekTarget: null
    property QtObject peeked: null
    property var savedOpacity: []
    // The order in which windows were opened (KWin gives none): an app's
    // cards keep it, like its taskbar group.
    property var openedOrder: ({})
    property int openedCount: 0

    readonly property bool below: button.y + button.height / 2 < screenArea.y + screenArea.height / 2
    readonly property real thumbWidth: {
        const n = Math.max(1, windows.length);
        const room = (screenArea.width - 2 * screenMargin - 2 * padding - (n - 1) * spacing) / n - 2 * cardPadding;
        return Math.min(maxThumbWidth, room);
    }
    readonly property real thumbHeight: Math.round(maxThumbWidth * 9 / 16) * thumbWidth / maxThumbWidth
    readonly property bool listMode: thumbWidth < minThumbWidth
    readonly property real cardWidth: thumbWidth + 2 * cardPadding
    readonly property real cardHeight: headerHeight + thumbHeight + cardPadding
    readonly property real flyoutWidth: listMode ? listWidth
                                                 : windows.length * cardWidth + Math.max(0, windows.length - 1) * spacing + 2 * padding
    readonly property real flyoutHeight: listMode ? Math.min(windows.length * rowHeight, screenArea.height * 0.6) + 2 * padding
                                                  : cardHeight + 2 * padding

    title: "VeltOS taskbar previews"
    flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
    color: "transparent"
    visible: false
    width: Math.ceil(flyoutWidth) + 2 * shadowMargin
    height: Math.ceil(flyoutHeight) + shadowMargin + gap
    x: Math.round(Math.max(screenArea.x + screenMargin - shadowMargin,
                           Math.min(button.x + button.width / 2 - width / 2,
                                    screenArea.x + screenArea.width - screenMargin - width + shadowMargin)))
    // The margin towards the taskbar is only the gap, so the window never
    // covers the taskbar's buttons.
    y: below ? button.y + button.height : button.y - height

    function rectEqual(a, b) {
        return a.x === b.x && a.y === b.y && a.width === b.width && a.height === b.height;
    }
    function contains(r, p) {
        return r.width > 0 && p.x >= r.x && p.x < r.x + r.width && p.y >= r.y && p.y < r.y + r.height;
    }
    function onCurrentDesktop(w) {
        if (w.onAllDesktops) {
            return true;
        }
        const current = KWin.Workspace.currentDesktop;
        return w.desktops.some(d => d === current);
    }
    function onCurrentActivity(w) {
        return w.activities.length === 0 || w.activities.indexOf(KWin.Workspace.currentActivity) >= 0;
    }
    function remember(w) {
        const id = w.internalId.toString();
        if (!(id in openedOrder)) {
            openedOrder[id] = ++openedCount;
        }
    }
    function byOpening(a, b) {
        return (openedOrder[a.internalId.toString()] || 0) - (openedOrder[b.internalId.toString()] || 0);
    }
    function onTaskbar(w) {
        return !w.deleted && !w.skipTaskbar && (w.normalWindow || w.dialog || w.utility)
            && onCurrentDesktop(w) && onCurrentActivity(w);
    }
    // The taskbar button under the point and its windows, or null.
    function buttonAt(p) {
        const order = KWin.Workspace.stackingOrder;
        let rect = null;
        for (let i = 0; i < order.length; ++i) {
            const w = order[i];
            if (contains(w.iconGeometry, p) && onTaskbar(w)) {
                rect = w.iconGeometry;
                break;
            }
        }
        if (rect === null) {
            return null;
        }
        return { rect: rect, windows: windowsOf(rect) };
    }
    function windowsOf(rect) {
        const list = [];
        const order = KWin.Workspace.stackingOrder;
        for (let i = 0; i < order.length; ++i) {
            const w = order[i];
            if (rectEqual(w.iconGeometry, rect) && onTaskbar(w)) {
                list.push(w);
            }
        }
        return list.sort(byOpening);
    }
    function insideFlyout(p) {
        return shown && p.x >= x + shadowMargin && p.x < x + width - shadowMargin
            && p.y >= y + (below ? gap : shadowMargin) && p.y < y + height - (below ? shadowMargin : gap);
    }

    function show(hit) {
        const screen = KWin.Workspace.screenAt(Qt.point(hit.rect.x + hit.rect.width / 2, hit.rect.y + hit.rect.height / 2));
        if (!screen) {
            return;
        }
        screenArea = screen.geometry;
        button = hit.rect;
        windows = hit.windows;
        candidate = null;
        if (!shown) {
            shown = true;
            disappear.stop();
            flyout.opacity = 0;
            flyout.offset = below ? -gap : gap;
            visible = true;
            appear.restart();
        }
    }
    function hide(suppress) {
        showTimer.stop();
        switchTimer.stop();
        hideTimer.stop();
        unpeek();
        peekTarget = null;
        candidate = null;
        if (suppress && shown) {
            suppressed = button;
        }
        if (shown) {
            shown = false;
            appear.stop();
            disappear.restart();
        }
    }
    function activate(w) {
        hide(true);
        if (w.minimized) {
            w.minimized = false;
        }
        KWin.Workspace.activeWindow = w;
    }
    function closeWindow(w) {
        unpeek();
        w.closeWindow();
    }

    function peek(w) {
        unpeek();
        if (w.minimized) {
            return; // Peek shows windows where they are; a minimized one is not on the screen.
        }
        const saved = [];
        const order = KWin.Workspace.stackingOrder;
        for (let i = 0; i < order.length; ++i) {
            const other = order[i];
            // Not these cards themselves: they stay, as on Windows.
            if (other !== w && !other.deleted && (other.normalWindow || other.dialog || other.utility)
                && !other.minimized && onCurrentDesktop(other) && other.caption !== preview.title) {
                saved.push({ window: other, opacity: other.opacity });
                other.opacity = 0;
            }
        }
        savedOpacity = saved;
        peeked = w;
    }
    function unpeek() {
        peekTimer.stop();
        for (const entry of savedOpacity) {
            if (!entry.window.deleted) {
                entry.window.opacity = entry.opacity;
            }
        }
        savedOpacity = [];
        peeked = null;
    }

    function pointerMoved() {
        const p = KWin.Workspace.cursorPos;
        if (insideFlyout(p)) {
            hideTimer.stop();
            switchTimer.stop();
            return;
        }
        const hit = buttonAt(p);
        if (hit === null) {
            showTimer.stop();
            switchTimer.stop();
            candidate = null;
            suppressed = Qt.rect(0, 0, 0, 0);
            if (shown && !hideTimer.running) {
                hideTimer.start();
            }
            return;
        }
        if (rectEqual(hit.rect, suppressed)) {
            return;
        }
        suppressed = Qt.rect(0, 0, 0, 0);
        if (shown) {
            hideTimer.stop();
            if (rectEqual(hit.rect, button)) {
                switchTimer.stop();
                candidate = null;
            } else if (candidate === null || !rectEqual(candidate.rect, hit.rect)) {
                candidate = hit;
                switchTimer.restart();
            }
        } else if (candidate === null || !rectEqual(candidate.rect, hit.rect)) {
            candidate = hit;
            showTimer.restart();
        }
    }
    // The shown button's windows again (one closed, one opened).
    function update() {
        if (!shown) {
            return;
        }
        const list = windowsOf(button);
        if (list.length === 0) {
            hide(false);
        } else {
            windows = list;
        }
    }

    Timer {
        id: showTimer
        interval: 400
        onTriggered: {
            const hit = preview.buttonAt(KWin.Workspace.cursorPos);
            if (hit !== null) {
                preview.show(hit);
            }
        }
    }
    Timer {
        id: switchTimer
        interval: 80
        onTriggered: {
            const hit = preview.buttonAt(KWin.Workspace.cursorPos);
            if (hit !== null) {
                preview.show(hit);
            }
        }
    }
    Timer {
        id: hideTimer
        interval: 300
        onTriggered: preview.hide(false)
    }
    Timer {
        id: peekTimer
        interval: 700
        onTriggered: {
            if (preview.peekTarget !== null) {
                preview.peek(preview.peekTarget);
            }
        }
    }
    Timer {
        id: refresh
        interval: 1
        onTriggered: preview.update()
    }
    Connections {
        target: KWin.Workspace
        function onCursorPosChanged() {
            preview.pointerMoved();
        }
        function onWindowActivated(w) {
            // A click on a single window's button activates or minimizes
            // it: the cards go (or do not come), as on Windows.
            preview.suppressPointedButton();
        }
        function onWindowAdded(w) {
            preview.remember(w);
            // The button's menu (right click) or another menu opened;
            // tooltips (the pinned apps' names) and these cards do not count.
            if (w.popupWindow && !w.tooltip && w.caption !== preview.title) {
                preview.suppressPointedButton();
            } else {
                refresh.restart();
            }
        }
        function onWindowRemoved(w) {
            if (preview.windows.indexOf(w) >= 0) {
                refresh.restart();
            }
        }
        function onCurrentDesktopChanged() {
            preview.hide(false);
        }
    }

    function suppressPointedButton() {
        if (peeked !== null) {
            return;
        }
        if (shown) {
            hide(true);
        } else if (candidate !== null) {
            suppressed = candidate.rect;
            showTimer.stop();
            candidate = null;
        }
    }

    Component.onCompleted: KWin.Workspace.stackingOrder.forEach(remember)
    Component.onDestruction: unpeek()

    // --- Flyout -----------------------------------------------------------

    ParallelAnimation {
        id: appear
        NumberAnimation { target: flyout; property: "opacity"; to: 1; duration: 140; easing.type: Easing.OutCubic }
        NumberAnimation { target: flyout; property: "offset"; to: 0; duration: 180; easing.type: Easing.OutCubic }
    }
    SequentialAnimation {
        id: disappear
        NumberAnimation { target: flyout; property: "opacity"; to: 0; duration: 100; easing.type: Easing.InCubic }
        ScriptAction {
            script: {
                if (!preview.shown) {
                    preview.visible = false;
                    preview.windows = [];
                }
            }
        }
    }

    Item {
        id: flyout
        property real offset: 0
        x: preview.shadowMargin
        y: (preview.below ? preview.gap : preview.shadowMargin) + offset
        width: preview.flyoutWidth
        height: preview.flyoutHeight

        Kirigami.ShadowedRectangle {
            anchors.fill: parent
            radius: 8
            color: Qt.alpha(Kirigami.Theme.backgroundColor, 0.98)
            border.width: 1
            border.color: Qt.alpha(Kirigami.Theme.textColor, 0.12)
            shadow.size: 14
            shadow.yOffset: 3
            shadow.color: Qt.rgba(0, 0, 0, 0.22)
        }

        // Cards side by side.
        Row {
            visible: !preview.listMode
            x: preview.padding
            y: preview.padding
            spacing: preview.spacing
            Repeater {
                model: preview.listMode ? [] : preview.windows
                delegate: card
            }
        }

        // Many windows: a list.
        Flickable {
            visible: preview.listMode
            x: preview.padding
            y: preview.padding
            width: parent.width - 2 * preview.padding
            height: parent.height - 2 * preview.padding
            contentHeight: listColumn.height
            clip: true
            Column {
                id: listColumn
                width: parent.width
                Repeater {
                    model: preview.listMode ? preview.windows : []
                    delegate: row
                }
            }
        }
    }

    // A window as a card: icon, title, close button, live picture.
    Component {
        id: card
        MouseArea {
            id: cardArea
            required property QtObject modelData
            readonly property QtObject window: modelData
            readonly property real aspect: window.width / Math.max(1, window.height)
            width: preview.cardWidth
            height: preview.cardHeight
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.MiddleButton
            onClicked: mouse => {
                if (mouse.button === Qt.MiddleButton) {
                    preview.closeWindow(window);
                } else {
                    preview.activate(window);
                }
            }
            onContainsMouseChanged: {
                if (containsMouse) {
                    preview.peekTarget = window;
                    peekTimer.restart();
                } else if (preview.peekTarget === window) {
                    preview.peekTarget = null;
                    preview.unpeek();
                }
            }
            Accessible.role: Accessible.Button
            Accessible.name: window.caption

            Rectangle {
                anchors.fill: parent
                radius: 6
                color: Kirigami.Theme.textColor
                opacity: cardArea.pressed ? 0.04 : (cardArea.containsMouse ? 0.07 : 0)
            }
            Kirigami.Icon {
                id: cardIcon
                x: preview.cardPadding
                y: (preview.headerHeight - height) / 2
                width: 16
                height: 16
                source: cardArea.window.icon
            }
            Text {
                anchors {
                    left: cardIcon.right
                    leftMargin: 8
                    right: cardClose.visible ? cardClose.left : parent.right
                    rightMargin: cardClose.visible ? 4 : preview.cardPadding
                    verticalCenter: cardIcon.verticalCenter
                }
                text: cardArea.window.caption
                color: Kirigami.Theme.textColor
                elide: Text.ElideRight
                maximumLineCount: 1
                font.family: Kirigami.Theme.defaultFont.family
                font.pixelSize: 12
            }
            CloseButton {
                id: cardClose
                anchors {
                    right: parent.right
                    rightMargin: 4
                    top: parent.top
                    topMargin: 4
                }
                visible: cardArea.containsMouse
                onClicked: preview.closeWindow(cardArea.window)
            }
            Item {
                id: thumbBox
                x: preview.cardPadding
                y: preview.headerHeight
                width: preview.thumbWidth
                height: preview.thumbHeight
                readonly property real fitWidth: Math.min(width, height * cardArea.aspect)
                KWin.WindowThumbnail {
                    anchors.centerIn: parent
                    width: thumbBox.fitWidth
                    height: thumbBox.fitWidth / cardArea.aspect
                    wId: cardArea.window.internalId
                    visible: !cardArea.window.minimized
                }
                // A minimized window has no picture on the screen: its icon.
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: 48
                    height: 48
                    source: cardArea.window.icon
                    visible: cardArea.window.minimized
                }
            }
        }
    }

    // A window as a list row: icon, title, close button.
    Component {
        id: row
        MouseArea {
            id: rowArea
            required property QtObject modelData
            readonly property QtObject window: modelData
            width: parent ? parent.width : preview.listWidth
            height: preview.rowHeight
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.MiddleButton
            onClicked: mouse => {
                if (mouse.button === Qt.MiddleButton) {
                    preview.closeWindow(window);
                } else {
                    preview.activate(window);
                }
            }
            onContainsMouseChanged: {
                if (containsMouse) {
                    preview.peekTarget = window;
                    peekTimer.restart();
                } else if (preview.peekTarget === window) {
                    preview.peekTarget = null;
                    preview.unpeek();
                }
            }
            Accessible.role: Accessible.Button
            Accessible.name: window.caption

            Rectangle {
                anchors.fill: parent
                radius: 6
                color: Kirigami.Theme.textColor
                opacity: rowArea.pressed ? 0.04 : (rowArea.containsMouse ? 0.07 : 0)
            }
            Kirigami.Icon {
                id: rowIcon
                x: 12
                anchors.verticalCenter: parent.verticalCenter
                width: 16
                height: 16
                source: rowArea.window.icon
            }
            Text {
                anchors {
                    left: rowIcon.right
                    leftMargin: 12
                    right: rowClose.left
                    rightMargin: 4
                    verticalCenter: parent.verticalCenter
                }
                text: rowArea.window.caption
                color: Kirigami.Theme.textColor
                elide: Text.ElideRight
                maximumLineCount: 1
                font.family: Kirigami.Theme.defaultFont.family
                font.pixelSize: 12
            }
            CloseButton {
                id: rowClose
                anchors {
                    right: parent.right
                    rightMargin: 6
                    verticalCenter: parent.verticalCenter
                }
                opacity: rowArea.containsMouse ? 1 : 0
                onClicked: preview.closeWindow(rowArea.window)
            }
        }
    }

    // Windows 11's close button: a plain cross, red when pointed at.
    component CloseButton: MouseArea {
        id: closeArea
        width: 28
        height: 24
        hoverEnabled: true
        Accessible.role: Accessible.Button
        Accessible.name: Qt.locale().name.startsWith("tr") ? "Kapat" : "Close"
        Rectangle {
            anchors.fill: parent
            radius: 4
            color: closeArea.pressed ? "#b62d1f" : "#c42b1c"
            visible: closeArea.containsMouse
        }
        Repeater {
            model: [45, -45]
            Rectangle {
                required property int modelData
                anchors.centerIn: parent
                width: 11
                height: 1
                antialiasing: true
                rotation: modelData
                color: closeArea.containsMouse ? "white" : Kirigami.Theme.textColor
            }
        }
    }
}
