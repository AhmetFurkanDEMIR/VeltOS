// Colours and sizes of VeltOS Weather: Windows 11 Weather's proportions in
// the VeltOS palette, light and dark as the system is.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    readonly property real textScale: backend.textScale

    readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color rail: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color card: dark ? "#272934" : "#FFFFFF"
    readonly property color cardHover: dark ? "#2F3240" : "#F7F8FC"
    readonly property color cardBorder: dark ? "#33364A" : "#E3E6EE"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color faint: dark ? "#7D8296" : "#8C92A3"
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color accentSoft: Qt.rgba(accent.r, accent.g, accent.b, dark ? 0.22 : 0.12)
    readonly property color navSelected: dark ? "#2C2F3D" : "#E4E8F3"
    readonly property color navHover: dark ? "#262835" : "#EBEEF6"
    readonly property color field: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color fieldBorder: dark ? "#3E4152" : "#D5DAE4"
    readonly property color track: dark ? "#3A3D4E" : "#E4E8F0"
    readonly property color menu: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color warning: dark ? "#433A1E" : "#FFF4CE"
    readonly property color warningText: dark ? "#F5E2A6" : "#5C4A00"

    readonly property int radius: 8
    readonly property int bigRadius: 12
    readonly property int titleSize: Math.round(28 * textScale)
    readonly property int headingSize: Math.round(20 * textScale)
    readonly property int subtitleSize: Math.round(16 * textScale)
    readonly property int bodySize: Math.round(14 * textScale)
    readonly property int captionSize: Math.round(12 * textScale)
    readonly property int heroSize: Math.round(76 * textScale)
}
