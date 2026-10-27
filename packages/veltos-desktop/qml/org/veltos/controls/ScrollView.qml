// VeltOS controls style: a scroll view with VeltOS' scroll bars (Breeze's
// own ScrollView would create Breeze's scroll bars, separator included).
// Smooth wheel scrolling through Kirigami as in Breeze. The bars are drawn
// over the content's edge, as Windows 11 draws them (thin until the pointer
// is on them): no space is set aside for them. Space kept free only while a
// bar was shown made the content narrower when the bar appeared; a page
// whose text then wrapped onto more lines (or fewer) made the bar come and
// go for ever and the app hung, VeltOS Settings maximised on the Home page
// among them (product owner, 2026-10-26).
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

    rightPadding: 0
    leftPadding: 0
    bottomPadding: 0

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
