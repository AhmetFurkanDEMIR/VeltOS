// Colours and sizes of VeltOS Notepad: Windows 11 Notepad's proportions in
// the VeltOS palette, light and dark (app setting or the system's).
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    // Settings > Accessibility > Text size: every text size below scales with it.
    readonly property real textScale: backend.textScale

    readonly property color tabStrip: dark ? "#1E1F27" : "#E9ECF2"     // title bar with the tabs
    readonly property color toolbar: dark ? "#272832" : "#F9FAFC"      // current tab and menu row
    readonly property color editor: dark ? "#22232C" : "#FFFFFF"
    readonly property color statusBar: dark ? "#1E1F27" : "#F3F5F9"
    readonly property color separator: dark ? "#34364A" : "#E1E4EB"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#A9AEC0" : "#5D6475"
    readonly property color disabled: dark ? "#5F6375" : "#B4B9C6"
    readonly property color hover: dark ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(0, 0, 0, 0.05)
    readonly property color pressed: dark ? Qt.rgba(1, 1, 1, 0.04) : Qt.rgba(0, 0, 0, 0.08)
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color accentText: dark ? "#0B1020" : "#FFFFFF"
    readonly property color selection: dark ? "#3A5BB8" : "#BFD3FB"
    readonly property color field: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color fieldBorder: dark ? "#3B3E4E" : "#D9DDE6"
    readonly property color menu: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
    readonly property color page: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color closeHover: "#C42B1C"

    readonly property int radius: 6
    readonly property int fontSize: Math.round(13 * textScale)
    readonly property int smallFont: Math.round(12 * textScale)
}
