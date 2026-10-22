// Colours and sizes of VeltOS Disk Management (the VeltOS Settings
// palette, Windows 11 proportions, Disk Management's partition colours).
// Follows the light/dark global theme and the accent colour.
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
    readonly property color rowHover: dark ? "#2E3140" : "#F0F2F8"
    readonly property color rowSelected: dark ? "#333648" : "#E4E8F3"
    readonly property color control: dark ? "#2E3140" : "#FBFCFE"
    readonly property color field: dark ? "#2E3140" : "#FFFFFF"
    readonly property color fieldBorder: dark ? "#4A4E60" : "#D6DAE3"
    readonly property color toolbar: dark ? "#23242F" : "#EEF0F6"
    readonly property color popup: dark ? "#2A2C38" : "#FFFFFF"

    // Disk Management's partition colours: the stripe over each volume.
    readonly property color primary: "#1F3A93"
    readonly property color logical: "#2FA8F0"
    readonly property color extended: "#2E8B57"
    readonly property color freeSpace: "#57C65C"
    readonly property color unallocated: dark ? "#0E0E12" : "#1A1A1A"
    readonly property color segmentBody: dark ? "#2A2C38" : "#FFFFFF"

    readonly property int radius: 8
    readonly property int titleSize: Math.round(20 * textScale)
    readonly property int bodySize: Math.round(12 * textScale)
    readonly property int smallSize: Math.round(11 * textScale)
    readonly property int rowHeight: Math.round(30 * textScale)
}
