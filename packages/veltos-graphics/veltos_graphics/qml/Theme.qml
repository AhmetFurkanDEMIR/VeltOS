// Colours and sizes of VeltOS Graphics Cards (the VeltOS Settings palette,
// Windows 11 proportions and InfoBar colours). Follows the light/dark
// global theme and the accent colour.
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
    readonly property color divider: dark ? "#363949" : "#ECEEF3"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color control: dark ? "#2E3140" : "#FBFCFE"
    readonly property color track: dark ? "#3A3D4E" : "#E1E5EE"

    // Windows 11 InfoBar: background and icon colour per severity.
    readonly property color infoBack: dark ? "#2E3140" : "#F4F6FB"
    readonly property color successBack: dark ? "#393D1B" : "#DFF6DD"
    readonly property color successIcon: dark ? "#6CCB5F" : "#0F7B0F"
    readonly property color warningBack: dark ? "#433519" : "#FFF4CE"
    readonly property color warningIcon: dark ? "#FCE100" : "#9D5D00"
    readonly property color errorBack: dark ? "#442726" : "#FDE7E9"
    readonly property color errorIcon: dark ? "#FF99A4" : "#C42B1C"

    readonly property int radius: 8
    readonly property int pageTitleSize: Math.round(28 * textScale)
    readonly property int nameSize: Math.round(18 * textScale)
    readonly property int sectionSize: Math.round(14 * textScale)
    readonly property int titleSize: Math.round(14 * textScale)
    readonly property int bodySize: Math.round(12 * textScale)
}
