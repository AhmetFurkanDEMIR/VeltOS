// Colours and sizes of VeltOS Settings (Windows 11 Settings proportions,
// VeltOS palette). Follows the light/dark global theme.
//
// The window's background is acrylic where KWin can blur behind it (what
// is behind, under `acrylicTint`; acrylic.py), else Mica (Main.qml): the
// desktop picture, blurred and covered by `micaTint`. Cards, the
// navigation highlight and controls are translucent layers on it, as in
// Windows 11 Settings, so what is behind shows faintly through the whole
// window (product owner, 2026-11-07). Surfaces drawn over other content
// (pop-ups, a slider's thumb, a focused text box) stay opaque.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode
    // Settings > Accessibility > Text size: every text size below scales with it.
    readonly property real textScale: backend.textScale

    // Mica: the colour shown while the picture loads (and without one), and
    // the layer over the blurred picture.
    readonly property color window: dark ? "#202128" : "#F3F4F8"
    readonly property color micaTint: dark ? Qt.rgba(0.118, 0.122, 0.149, 0.80) : Qt.rgba(0.953, 0.957, 0.969, 0.80)
    // Acrylic (Transparency effects on, KWin blurring behind the window):
    // the windows and desktop behind show through, as behind Start.
    readonly property color acrylicTint: dark ? Qt.rgba(0.118, 0.122, 0.149, 0.70) : Qt.rgba(0.953, 0.957, 0.969, 0.68)

    readonly property color card: dark ? Qt.rgba(1, 1, 1, 0.055) : Qt.rgba(1, 1, 1, 0.72)
    readonly property color cardHover: dark ? Qt.rgba(1, 1, 1, 0.085) : Qt.rgba(1, 1, 1, 0.50)
    readonly property color cardPressed: dark ? Qt.rgba(1, 1, 1, 0.035) : Qt.rgba(1, 1, 1, 0.32)
    readonly property color cardBorder: dark ? Qt.rgba(0, 0, 0, 0.28) : Qt.rgba(0, 0, 0, 0.075)
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#B4B8C8" : "#5D6475"
    // The user's accent colour (Personalization > Colours), lightened in
    // dark mode for contrast, as Windows does.
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color navSelected: dark ? Qt.rgba(1, 1, 1, 0.065) : Qt.rgba(0, 0, 0, 0.045)
    readonly property color navHover: dark ? Qt.rgba(1, 1, 1, 0.045) : Qt.rgba(0, 0, 0, 0.03)
    readonly property color track: dark ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(0, 0, 0, 0.11)
    readonly property color trackStrong: dark ? "#5A5E72" : "#8A90A2"
    readonly property color control: dark ? Qt.rgba(1, 1, 1, 0.06) : Qt.rgba(1, 1, 1, 0.70)
    readonly property color popup: dark ? "#2C2D35" : "#FFFFFF"
    // A text box being typed in, a slider's thumb: opaque, as on Windows 11.
    readonly property color field: dark ? "#1E1F26" : "#FFFFFF"
    readonly property color danger: dark ? "#FF99A4" : "#C42B1C"
    // Title bar buttons.
    readonly property color hover: dark ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.05)
    readonly property color closeHover: "#C42B1C"

    readonly property int radius: 8
    readonly property int pageTitleSize: Math.round(28 * textScale)
    readonly property int sectionSize: Math.round(14 * textScale)
    readonly property int titleSize: Math.round(14 * textScale)
    readonly property int bodySize: Math.round(12 * textScale)
}
