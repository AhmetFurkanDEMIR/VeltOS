// Colours and sizes of VeltOS PDF Reader in the VeltOS palette, light and
// dark (app setting or the system's).
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    // Settings > Accessibility > Text size: every text size below scales with it.
    readonly property real textScale: backend.textScale

    readonly property color window: dark ? "#1C1D25" : "#F1F3F8"       // Mica: title bar and pane
    readonly property color content: dark ? "#23242D" : "#F9FAFC"      // gallery and viewer
    readonly property color statusBar: dark ? "#1E1F27" : "#F3F5F9"
    readonly property color separator: dark ? "#34364A" : "#E1E4EB"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#A9AEC0" : "#5D6475"
    readonly property color disabled: dark ? "#5F6375" : "#B4B9C6"
    readonly property color hover: dark ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(0, 0, 0, 0.05)
    readonly property color pressed: dark ? Qt.rgba(1, 1, 1, 0.04) : Qt.rgba(0, 0, 0, 0.08)
    readonly property color selected: dark ? Qt.rgba(1, 1, 1, 0.09) : Qt.rgba(0, 0, 0, 0.06)
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color accentText: dark ? "#0B1020" : "#FFFFFF"
    readonly property color field: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color fieldBorder: dark ? "#3B3E4E" : "#D9DDE6"
    readonly property color menu: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
    readonly property color zebra: dark ? Qt.rgba(1, 1, 1, 0.03) : Qt.rgba(0, 0, 0, 0.03)
    readonly property color tile: dark ? "#2E3040" : "#E7EAF1"         // picture still loading
    readonly property color player: dark ? "#202129" : "#F7F8FB"         // the player bar
    readonly property color heart: "#E3365B"
    readonly property color closeHover: "#C42B1C"

    readonly property int radius: 6
    readonly property int fontSize: Math.round(13 * textScale)
    readonly property int smallFont: Math.round(12 * textScale)
}
