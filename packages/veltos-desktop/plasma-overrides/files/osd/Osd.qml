/*
    VeltOS on-screen display (volume, brightness, keyboard layout ...): the
    flyout at the bottom of the screen, as Windows 11 shows it. plasmashell
    loads osd/Osd.qml from the desktop shell package (plasma-workspace 6.3,
    shell/osd.cpp; not from the global theme) and sets the same properties
    as on Plasma's own. KWin places an OSD window with its centre at two
    thirds of the screen: the window is tall enough for its bottom edge,
    where the flyout sits, to end just above the taskbar; the rest is empty
    and click-through (outputOnly).
    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick
import org.kde.plasma.core as PlasmaCore

PlasmaCore.Dialog {
    id: dialog
    location: PlasmaCore.Types.Floating
    type: PlasmaCore.Dialog.OnScreenDisplay
    outputOnly: true
    backgroundHints: PlasmaCore.Dialog.NoBackground
    LayoutMirroring.enabled: Qt.application.layoutDirection === Qt.RightToLeft
    LayoutMirroring.childrenInherit: true

    property alias timeout: osd.timeout
    property alias osdValue: osd.osdValue
    property alias osdMaxValue: osd.osdMaxValue
    property alias osdAdditionalText: osd.osdAdditionalText
    property alias icon: osd.icon
    property alias showingProgress: osd.showingProgress

    onVisibleChanged: if (visible) osd.enter()

    mainItem: OsdItem {
        id: osd
        // The window's own screen (the item's attached Screen is empty
        // while the window is first sized).
        windowScreenHeight: dialog.screen ? dialog.screen.desktopAvailableHeight : 0
    }
}
