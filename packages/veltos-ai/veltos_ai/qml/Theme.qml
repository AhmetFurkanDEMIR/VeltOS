// Colours and sizes of VeltOS AI's pane: Windows 11 Copilot's proportions in
// the VeltOS palette, light and dark as the system is.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    readonly property real textScale: backend.textScale

    readonly property color window: dark ? "#1D1F29" : "#F4F6FB"
    readonly property color edge: dark ? "#33364A" : "#DCE0EA"
    readonly property color card: dark ? "#282A36" : "#FFFFFF"
    readonly property color cardHover: dark ? "#30333F" : "#F8F9FD"
    readonly property color cardBorder: dark ? "#353849" : "#E2E6EF"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color faint: dark ? "#7D8296" : "#8C92A3"
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color accentText: "#FFFFFF"
    readonly property color hover: dark ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(0, 0, 0, 0.05)
    readonly property color field: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color fieldBorder: dark ? "#40435A" : "#D3D8E3"
    readonly property color danger: dark ? "#FF99A4" : "#C42B1C"
    readonly property color dangerSoft: dark ? "#3A2329" : "#FDE7E9"
    readonly property color success: dark ? "#6CCB5F" : "#0F7B0F"
    // The VeltOS AI colours (the icon's): blue to violet.
    readonly property color brandA: "#4F7CFF"
    readonly property color brandB: "#8A4FFF"

    readonly property int radius: 8
    readonly property int bubbleRadius: 14
    readonly property int titleSize: Math.round(22 * textScale)
    readonly property int headingSize: Math.round(16 * textScale)
    readonly property int bodySize: Math.round(14 * textScale)
    readonly property int captionSize: Math.round(12 * textScale)
}
