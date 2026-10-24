// VeltOS controls style: a scroll view with VeltOS' scroll bars (Breeze's
// own ScrollView would create Breeze's scroll bars, separator included).
// Smooth wheel scrolling through Kirigami as in Breeze; space for the bar
// is kept free only while it is shown.
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Templates as T
import org.kde.kirigami as Kirigami

T.ScrollView {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            contentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             contentHeight + topPadding + bottomPadding)

    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: !background || !background.visible

    data: [
        Kirigami.WheelHandler {
            target: control.contentItem
        }
    ]

    rightPadding: !mirrored && ScrollBar.vertical && ScrollBar.vertical.visible ? ScrollBar.vertical.width : 0
    leftPadding: mirrored && ScrollBar.vertical && ScrollBar.vertical.visible ? ScrollBar.vertical.width : 0
    bottomPadding: ScrollBar.horizontal && ScrollBar.horizontal.visible ? ScrollBar.horizontal.height : 0

    ScrollBar.vertical: ScrollBar {
        parent: control
        x: control.mirrored ? 0 : control.width - width
        y: control.topPadding
        height: control.availableHeight
        active: control.ScrollBar.horizontal.active
    }

    ScrollBar.horizontal: ScrollBar {
        parent: control
        x: control.leftPadding
        y: control.height - height
        width: control.availableWidth
        active: control.ScrollBar.vertical.active
    }
}
