// Colours and sizes of VeltOS Archive (the VeltOS Settings palette,
// Windows 11 proportions). Follows the light/dark global theme.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode

    readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color bar: dark ? "#22242E" : "#FAFBFD"
    readonly property color list: dark ? "#1F2029" : "#FFFFFF"
    readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
    readonly property color divider: dark ? "#2F3240" : "#E8EBF2"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color disabledText: dark ? "#5E6273" : "#A9AEBB"
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color accentText: dark ? "#0B1020" : "#FFFFFF"
    readonly property color hover: dark ? Qt.rgba(1, 1, 1, 0.06) : Qt.rgba(0, 0, 0, 0.04)
    readonly property color pressed: dark ? Qt.rgba(1, 1, 1, 0.04) : Qt.rgba(0, 0, 0, 0.07)
    readonly property color selected: dark ? Qt.rgba(0.43, 0.58, 1, 0.22) : Qt.rgba(0.18, 0.37, 0.9, 0.12)
    readonly property color control: dark ? "#2E3140" : "#FBFCFE"
    readonly property color controlHover: dark ? "#353849" : "#F6F7FB"
    readonly property color scrim: Qt.rgba(0, 0, 0, dark ? 0.45 : 0.3)
    readonly property color danger: dark ? "#FF99A4" : "#C42B1C"

    readonly property int radius: 8
    readonly property int smallRadius: 4
    readonly property int bodySize: 13
    readonly property int captionSize: 12
}
