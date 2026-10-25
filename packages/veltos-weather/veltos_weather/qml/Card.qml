// A Windows 11 card: rounded, a hairline border, the page's card colour.
import QtQuick
import "."

Rectangle {
    radius: Theme.radius
    color: Theme.card
    border.width: 1
    border.color: Theme.cardBorder
}
