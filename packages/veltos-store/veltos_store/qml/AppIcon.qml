// An app's icon: the AppStream picture (file:// address) or a theme icon
// name; a generic program icon when there is none.
import QtQuick
import org.kde.kirigami as Kirigami

Kirigami.Icon {
    property string icon: ""
    source: icon !== "" ? icon : "application-x-executable"
    fallback: "application-x-executable"
    smooth: true
}
