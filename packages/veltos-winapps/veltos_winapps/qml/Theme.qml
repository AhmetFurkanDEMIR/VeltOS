// Colours and sizes of the Windows program runner (the VeltOS Settings and
// Store palette, Windows 11 App Installer proportions). Follows the
// light/dark global theme.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: runner.darkMode

    readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color accent: runner.accent !== ""
                                    ? (dark ? Qt.lighter(runner.accent, 1.35) : runner.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color accentText: dark ? "#0B1020" : "#FFFFFF"
    readonly property color control: dark ? "#2E3140" : "#FBFCFE"
    readonly property color controlHover: dark ? "#353849" : "#F6F7FB"
    readonly property color controlBorder: dark ? "#8F94A6" : "#8A8F9C"
    readonly property color track: dark ? "#3A3D4E" : "#E1E5EE"
    readonly property color success: dark ? "#6CCB5F" : "#0F7B0F"
    readonly property color danger: dark ? "#FF99A4" : "#C42B1C"

    readonly property int radius: 8
    readonly property int smallRadius: 4
    readonly property int titleSize: 24
    readonly property int bodySize: 14
    readonly property int captionSize: 12
}
