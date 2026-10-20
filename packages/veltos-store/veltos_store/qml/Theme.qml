// Colours and sizes of VeltOS Store (VeltOS Settings palette, Microsoft
// Store proportions). Follows the light/dark global theme.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode

    readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color pane: dark ? "#20212B" : "#F8F9FC"
    readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
    readonly property color cardHover: dark ? "#323544" : "#F8F9FD"
    readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color accentText: dark ? "#0B1020" : "#FFFFFF"
    readonly property color navSelected: dark ? "#2C2F3D" : "#E4E8F3"
    readonly property color navHover: dark ? "#262835" : "#EBEEF6"
    readonly property color control: dark ? "#2E3140" : "#FBFCFE"
    readonly property color controlHover: dark ? "#353849" : "#F6F7FB"
    readonly property color track: dark ? "#3A3D4E" : "#E1E5EE"
    readonly property color danger: dark ? "#FF99A4" : "#C42B1C"

    readonly property int radius: 8
    readonly property int smallRadius: 4
    readonly property int pageTitleSize: 28
    readonly property int sectionSize: 20
    readonly property int bodySize: 13
    readonly property int captionSize: 12
}
