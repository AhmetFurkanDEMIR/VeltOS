// Colours, sizes and animation timing of the VeltOS Office start pages,
// after Microsoft 365's "Colorful" theme (light) and "Black" theme (dark)
// on Windows 11: the title bar and the navigation rail in the app's colour
// (Word blue, Excel green, PowerPoint orange), the pages light grey.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    // Settings > Accessibility > Text size: every text size below scales with it.
    readonly property real textScale: backend.textScale
    // Settings > Accessibility > Visual effects: 0 switches the animations off.
    readonly property real anim: backend.animations ? 1 : 0
    readonly property string kind: backend.kindName

    readonly property color brand: backend.brand
    readonly property color accent: backend.accent
    readonly property color chrome: dark ? "#1F1F1F" : brand
    readonly property color chromeText: "#FFFFFF"
    readonly property color chromeDim: Qt.rgba(1, 1, 1, 0.78)
    readonly property color chromeHover: Qt.rgba(1, 1, 1, dark ? 0.08 : 0.13)
    readonly property color chromePressed: Qt.rgba(1, 1, 1, dark ? 0.05 : 0.09)
    readonly property color chromeSelected: Qt.rgba(1, 1, 1, dark ? 0.12 : 0.2)

    readonly property color page: dark ? "#292929" : "#F7F7F9"
    readonly property color card: dark ? "#333335" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#48484C" : "#E2E3E8"
    readonly property color cardShadow: Qt.rgba(0, 0, 0, dark ? 0.5 : 0.12)
    readonly property color text: dark ? "#F3F3F5" : "#1B1B1F"
    readonly property color subtext: dark ? "#B4B4BA" : "#5F6069"
    readonly property color disabled: dark ? "#6E6E74" : "#B5B6BE"
    readonly property color hover: dark ? "#39393C" : "#ECEDF1"
    readonly property color pressed: dark ? "#414144" : "#E3E4E9"
    readonly property color separator: dark ? "#454548" : "#E5E6EA"
    readonly property color field: dark ? "#3A3A3D" : "#FFFFFF"
    readonly property color fieldBorder: dark ? "#55555A" : "#D6D7DE"
    readonly property color menu: dark ? "#2F2F32" : "#FFFFFF"
    readonly property color link: accent
    readonly property color closeHover: "#C42B1C"
    readonly property color thumbPage: "#FFFFFF"

    readonly property int radius: 6
    readonly property int fontSize: Math.round(14 * textScale)
    readonly property int smallFont: Math.round(12 * textScale)
    readonly property int sectionFont: Math.round(16 * textScale)
    readonly property int greetingFont: Math.round(28 * textScale)
    readonly property int titleFont: Math.round(24 * textScale)
    readonly property int railWidth: Math.round(176 * Math.min(1.3, textScale))
    readonly property int titleBarHeight: 32
    readonly property int rowHeight: Math.round(46 * textScale)

    // Template thumbnails: a portrait page, a landscape sheet, a 16:9 slide.
    readonly property real thumbRatio: kind === "word" ? 1.294 : (kind === "sheet" ? 0.72 : 0.5625)
    readonly property int tileWidth: kind === "word" ? 148 : 176
}
