// Colours, sizes and timing of VeltOS Mail, after Windows 11's new
// Outlook (Fluent 2): the brand blue header, white cards on a light grey
// canvas, the brand colour for selections and unread mail; a dark theme
// with the same structure.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    readonly property real textScale: backend.textScale
    // Settings > Accessibility > Visual effects: 0 switches animations off.
    readonly property real anim: backend.animations ? 1 : 0

    readonly property color brand: "#0F6CBD"
    readonly property color brandHover: "#115EA3"
    readonly property color brandPressed: "#0F548C"
    readonly property color brandText: dark ? "#479EF5" : "#0F6CBD"     // links, unread subjects
    readonly property color brandSoft: dark ? "#0E2A47" : "#EBF3FC"     // selected row
    readonly property color brandSoftHover: dark ? "#123659" : "#CFE4FA"

    readonly property color header: dark ? "#1F1F1F" : brand
    readonly property color headerText: "#FFFFFF"
    readonly property color headerHover: Qt.rgba(1, 1, 1, dark ? 0.08 : 0.12)
    readonly property color headerPressed: Qt.rgba(1, 1, 1, dark ? 0.05 : 0.2)

    readonly property color canvas: dark ? "#1A1A1A" : "#F0F0F0"
    readonly property color card: dark ? "#292929" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#333333" : "#E0E0E0"
    readonly property color text: dark ? "#FFFFFF" : "#242424"
    readonly property color subtext: dark ? "#ADADAD" : "#616161"
    readonly property color tertiary: dark ? "#8F8F8F" : "#707070"
    readonly property color disabled: dark ? "#5C5C5C" : "#BDBDBD"
    readonly property color hover: dark ? "#333333" : "#F5F5F5"
    readonly property color hoverCanvas: dark ? "#2E2E2E" : "#E6E6E6"
    readonly property color pressed: dark ? "#3D3D3D" : "#E0E0E0"
    readonly property color selectedFolder: dark ? "#383838" : "#E1E1E1"
    readonly property color separator: dark ? "#3D3D3D" : "#E6E6E6"
    readonly property color field: dark ? "#292929" : "#FFFFFF"
    readonly property color fieldBorder: dark ? "#666666" : "#D1D1D1"
    readonly property color fieldUnderline: dark ? "#ADADAD" : "#616161"
    readonly property color menu: dark ? "#2E2E2E" : "#FFFFFF"
    readonly property color warning: dark ? "#3D2E00" : "#FFF9E5"
    readonly property color warningBorder: dark ? "#6B5300" : "#FCE8B2"
    readonly property color danger: "#C50F1F"
    readonly property color flag: "#C50F1F"
    readonly property color closeHover: "#C42B1C"
    readonly property color shadowColour: Qt.rgba(0, 0, 0, dark ? 0.45 : 0.14)

    readonly property int radius: 4
    readonly property int cardRadius: 8
    readonly property string fontFamily: "Segoe UI"
    readonly property int fontSize: Math.round(14 * textScale)
    readonly property int smallFont: Math.round(12 * textScale)
    readonly property int captionFont: Math.round(11 * textScale)
    readonly property int subjectFont: Math.round(20 * textScale)
    readonly property int titleFont: Math.round(24 * textScale)
    readonly property int headerHeight: 48
    readonly property int railWidth: 48
    readonly property int rowHeight: Math.round(32 * textScale)
}
