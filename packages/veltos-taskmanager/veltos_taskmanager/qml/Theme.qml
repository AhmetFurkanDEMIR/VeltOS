// Colours and sizes of VeltOS Task Manager (VeltOS Settings palette,
// Windows 11 proportions). Follows the light/dark global theme.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    // Settings > Accessibility > Text size: every text size below scales with it.
    readonly property real textScale: backend.textScale

    readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color navSelected: dark ? "#2C2F3D" : "#E4E8F3"
    readonly property color navHover: dark ? "#262835" : "#EBEEF6"
    readonly property color rowHover: dark ? "#2A2C38" : "#F0F2F8"
    readonly property color rowSelected: dark ? "#333648" : "#E4E8F3"
    readonly property color control: dark ? "#2E3140" : "#FBFCFE"
    // Windows colours busy CPU/memory cells from pale to strong amber.
    function heat(percent) {
        const a = Math.min(1, Math.max(0, percent / 60));
        return dark ? Qt.rgba(0.95, 0.65, 0.15, 0.08 + 0.45 * a)
                    : Qt.rgba(1.0, 0.85, 0.35, 0.18 + 0.6 * a);
    }

    readonly property int radius: 8
    readonly property int pageTitleSize: Math.round(20 * textScale)
    readonly property int bodySize: Math.round(12 * textScale)
}
