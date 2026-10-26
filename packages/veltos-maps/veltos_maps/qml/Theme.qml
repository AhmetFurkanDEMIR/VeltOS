pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    readonly property real textScale: backend.textScale

    readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color card: dark ? "#272934" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#33364A" : "#E3E6EE"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color accentSoft: Qt.rgba(accent.r, accent.g, accent.b, dark ? 0.22 : 0.12)
    readonly property color field: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color fieldBorder: dark ? "#3E4152" : "#D5DAE4"
    readonly property int radius: 8
    readonly property int bodySize: Math.round(14 * textScale)
    readonly property int captionSize: Math.round(12 * textScale)
}
