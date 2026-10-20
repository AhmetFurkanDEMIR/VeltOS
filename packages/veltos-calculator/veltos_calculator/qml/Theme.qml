// Colours and sizes of VeltOS Calculator: Windows 11 Calculator
// proportions in the VeltOS palette (as VeltOS Settings). Follows the
// light/dark theme of the app setting or the system.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: backend.darkMode

    readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
    readonly property color pane: dark ? "#25262F" : "#FBFCFE"           // navigation, flyouts
    readonly property color paneBorder: dark ? "#353849" : "#E3E6EE"
    readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color disabledText: dark ? "#5E6273" : "#A9AEBB"
    readonly property color accent: backend.accent !== ""
                                    ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                    : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color accentText: dark ? "#0B1020" : "#FFFFFF"
    readonly property color hover: dark ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(0, 0, 0, 0.05)
    readonly property color pressed: dark ? Qt.rgba(1, 1, 1, 0.04) : Qt.rgba(0, 0, 0, 0.08)
    readonly property color selected: dark ? Qt.rgba(1, 1, 1, 0.09) : Qt.rgba(0, 0, 0, 0.06)
    readonly property color scrim: dark ? Qt.rgba(0, 0, 0, 0.35) : Qt.rgba(0, 0, 0, 0.18)

    // Keypad: digits lighter than the operators, "=" in the accent colour.
    readonly property color number: dark ? "#3A3C49" : "#FFFFFF"
    readonly property color numberHover: dark ? "#424555" : "#F8F9FB"
    readonly property color numberPressed: dark ? "#33353F" : "#F1F3F7"
    readonly property color operator: dark ? "#2E303C" : "#F8F9FC"
    readonly property color operatorHover: dark ? "#373948" : "#F0F2F6"
    readonly property color operatorPressed: dark ? "#2A2C36" : "#E9ECF2"
    readonly property color keyBorder: dark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(0, 0, 0, 0.06)
    readonly property color keyShade: dark ? Qt.rgba(0, 0, 0, 0.18) : Qt.rgba(0, 0, 0, 0.10)

    readonly property int radius: 8
    readonly property int keyRadius: 4
    readonly property int bodySize: 14
    readonly property int captionSize: 12
}
