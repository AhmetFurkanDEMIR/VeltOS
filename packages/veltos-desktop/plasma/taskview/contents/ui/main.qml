/*
    VeltOS Task View: the Windows 11 taskbar button that shows every open
    window and the virtual desktops. It starts the VeltOS Task View effect
    (kwin/effects/veltostaskview, the same as Meta+Tab).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import QtQuick.Shapes
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    function showOverview() {
        launcher.connectSource("dbus-send --session --type=method_call --dest=org.kde.kglobalaccel "
                               + "/component/kwin org.kde.kglobalaccel.Component.invokeShortcut "
                               + "string:'VeltOS Task View'");
    }

    P5Support.DataSource {
        id: launcher
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }

    preferredRepresentation: fullRepresentation
    toolTipMainText: i18n("Task View")
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    fullRepresentation: MouseArea {
        id: button

        readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
        // Settings > Personalization > Taskbar > Task view (shown or not).
        readonly property bool shown: Plasmoid.configuration.shown
        visible: shown
        Layout.minimumWidth: !shown ? 0 : vertical ? -1 : height
        Layout.minimumHeight: !shown ? 0 : vertical ? width : -1
        Layout.maximumWidth: Layout.minimumWidth
        Layout.maximumHeight: Layout.minimumHeight
        hoverEnabled: true
        onClicked: root.showOverview()
        Accessible.role: Accessible.Button
        Accessible.name: i18n("Task View")

        Rectangle {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            radius: Kirigami.Units.cornerRadius
            color: Kirigami.Theme.textColor
            opacity: button.pressed ? 0.12 : (button.containsMouse ? 0.07 : 0)
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
        }

        // Two overlapping windows, Windows 11's Task View glyph: outlines only,
        // the back window's lines stop at the front one, and the inside is
        // the taskbar showing through (it was filled with the Plasma theme's
        // opaque background, a black block in dark mode; product owner,
        // 2026-10-22). Drawn on a 16-unit grid and scaled.
        Shape {
            id: glyph
            anchors.centerIn: parent
            width: Kirigami.Units.iconSizes.smallMedium
            height: width
            preferredRendererType: Shape.CurveRenderer
            readonly property real unit: width / 16

            ShapePath {
                strokeColor: Kirigami.Theme.textColor
                strokeWidth: 1.3 * glyph.unit
                fillColor: "transparent"
                capStyle: ShapePath.RoundCap
                joinStyle: ShapePath.RoundJoin
                scale: Qt.size(glyph.unit, glyph.unit)
                // The back window: only the parts not behind the front one.
                PathSvg { path: "M 4.6 5 L 4.6 3.2 A 2 2 0 0 1 6.6 1.2 L 13.2 1.2 A 2 2 0 0 1 15.2 3.2 L 15.2 9.2 A 2 2 0 0 1 13.2 11.2 L 12.4 11.2" }
            }
            ShapePath {
                strokeColor: Kirigami.Theme.textColor
                strokeWidth: 1.3 * glyph.unit
                fillColor: "transparent"
                joinStyle: ShapePath.RoundJoin
                scale: Qt.size(glyph.unit, glyph.unit)
                // The front window.
                PathSvg { path: "M 2.8 5.4 L 10.2 5.4 A 2 2 0 0 1 12.2 7.4 L 12.2 12.8 A 2 2 0 0 1 10.2 14.8 L 2.8 14.8 A 2 2 0 0 1 0.8 12.8 L 0.8 7.4 A 2 2 0 0 1 2.8 5.4 Z" }
            }
        }
    }
}
