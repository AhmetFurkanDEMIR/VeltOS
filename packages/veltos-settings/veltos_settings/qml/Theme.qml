// Colours and sizes of VeltOS Settings (Windows 11 Settings proportions,
// VeltOS palette). Follows the light/dark global theme.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    // Settings > Accessibility > Text size: every text size below scales with it.
    readonly property real textScale: backend.textScale

    readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
    readonly property color cardHover: dark ? "#323544" : "#F8F9FD"
    readonly property color cardPressed: dark ? "#272935" : "#F0F2F8"
    readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    // The user's accent colour (Personalization > Colours), lightened in
    // dark mode for contrast, as Windows does.
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color navSelected: dark ? "#2C2F3D" : "#E4E8F3"
    readonly property color navHover: dark ? "#262835" : "#EBEEF6"
    readonly property color track: dark ? "#3A3D4E" : "#E1E5EE"
    readonly property color trackStrong: dark ? "#5A5E72" : "#8A90A2"
    readonly property color control: dark ? "#2E3140" : "#FBFCFE"
    readonly property color popup: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color danger: dark ? "#FF99A4" : "#C42B1C"

    readonly property int radius: 8
    readonly property int pageTitleSize: Math.round(28 * textScale)
    readonly property int sectionSize: Math.round(14 * textScale)
    readonly property int titleSize: Math.round(14 * textScale)
    readonly property int bodySize: Math.round(12 * textScale)
}
