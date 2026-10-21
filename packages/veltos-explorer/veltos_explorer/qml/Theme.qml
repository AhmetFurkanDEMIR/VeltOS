// Colours and sizes of VeltOS File Explorer, in the proportions of
// Windows 11 File Explorer (light and dark).
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    // Settings > Accessibility > Text size: every text size below scales with it.
    readonly property real textScale: backend.textScale

    readonly property color titleBar: dark ? "#1F2029" : "#E8EBF2"
    readonly property color toolbar: dark ? "#272833" : "#F7F8FB"
    readonly property color pane: dark ? "#272833" : "#F7F8FB"
    readonly property color content: dark ? "#1C1D25" : "#FFFFFF"
    readonly property color separator: dark ? "#363846" : "#E3E6EC"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#A9AEC0" : "#5D6475"
    readonly property color disabled: dark ? "#5F6375" : "#B4B9C6"
    readonly property color hover: dark ? "#2F3140" : "#EEF1F7"
    readonly property color pressed: dark ? "#363949" : "#E4E8F1"
    readonly property color selected: dark ? "#2E3F66" : "#DCE8FD"
    readonly property color selectedHover: dark ? "#34497A" : "#CCDDFB"
    readonly property color selectedBorder: dark ? "#4C6FC4" : "#9FC0F7"
    readonly property color accent: dark ? "#6E95FF" : "#2F5EE6"
    readonly property color field: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color fieldBorder: dark ? "#3B3E4E" : "#D9DDE6"
    readonly property color menu: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color closeHover: "#C42B1C"

    readonly property int radius: 6
    readonly property int fontSize: Math.round(13 * textScale)
    readonly property int smallFont: Math.round(12 * textScale)
    readonly property int rowHeight: 30
}
