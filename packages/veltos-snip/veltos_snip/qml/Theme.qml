// Colours and sizes of VeltOS Snipping Tool (the VeltOS Settings palette,
// Windows 11 proportions). Follows the light/dark global theme.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode

    readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color canvas: dark ? "#16171E" : "#E9ECF3"
    readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
    readonly property color bar: dark ? "#2B2D39" : "#FAFBFD"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color accentText: dark ? "#0B1020" : "#FFFFFF"
    readonly property color hover: dark ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(0, 0, 0, 0.05)
    readonly property color pressed: dark ? Qt.rgba(1, 1, 1, 0.04) : Qt.rgba(0, 0, 0, 0.08)
    readonly property color selected: dark ? Qt.rgba(1, 1, 1, 0.10) : Qt.rgba(0, 0, 0, 0.07)
    readonly property color control: dark ? "#2E3140" : "#FBFCFE"
    readonly property color controlHover: dark ? "#353849" : "#F6F7FB"
    // The screen behind the selection, as dim as Windows makes it.
    readonly property color dim: Qt.rgba(0, 0, 0, 0.45)

    readonly property int radius: 8
    readonly property int smallRadius: 4
    readonly property int bodySize: 13
    readonly property int captionSize: 12
}
