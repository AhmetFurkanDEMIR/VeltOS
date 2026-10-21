// Back / forward / recent / up, the address box (clickable path; click the
// empty part or press Ctrl+L to type a path) and the search box, as in
// Windows 11 File Explorer.
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: bar

    readonly property var tab: backend.current
    property bool editing: false

    function editAddress() {
        editing = true;
        pathInput.text = tab.kind === "folder" ? tab.location : "";
        pathInput.forceActiveFocus();
        pathInput.selectAll();
    }
    function focusSearch() {
        searchInput.forceActiveFocus();
        searchInput.selectAll();
    }

    implicitHeight: 48
    color: Theme.toolbar

    Connections {
        target: backend
        function onCurrentChanged() {
            bar.editing = false;
            searchInput.text = bar.tab.query;
        }
    }
    Connections {
        target: bar.tab
        function onChanged() {
            if (!searchInput.activeFocus)
                searchInput.text = bar.tab.query;
        }
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 1
        color: Theme.separator
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 12
        spacing: 2

        IconButton {
            icon: "go-previous"
            tooltip: backend.text("back") + " (Alt+Left)"
            enabledState: bar.tab.canBack
            onClicked: bar.tab.back()
        }
        IconButton {
            icon: "go-next"
            tooltip: backend.text("forward") + " (Alt+Right)"
            enabledState: bar.tab.canForward
            onClicked: bar.tab.forward()
        }
        IconButton {
            id: recentButton
            icon: "arrow-down"
            iconSize: 12
            enabledState: bar.tab.recentLocations.length > 0
            onClicked: recentMenu.openAt(recentButton, 0, recentButton.height + 4)
        }
        IconButton {
            icon: "go-up"
            tooltip: backend.text("up").replace("{name}", "") + " (Alt+Up)"
            enabledState: bar.tab.canUp
            onClicked: bar.tab.up()
        }

        // Address box
        Rectangle {
            id: addressBox
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            Layout.leftMargin: 6
            radius: 4
            color: Theme.field
            border.width: 1
            border.color: bar.editing ? Theme.accent : Theme.fieldBorder

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 4
                spacing: 4
                visible: !bar.editing

                Kirigami.Icon {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    source: bar.tab.query !== "" ? "search" : bar.tab.icon
                }
                Repeater {
                    model: bar.tab.query !== ""
                           ? [{ name: backend.format("search_results", "name", bar.tab.title), location: "" }]
                           : bar.tab.crumbs
                    delegate: RowLayout {
                        required property var modelData
                        spacing: 0
                        Kirigami.Icon {
                            Layout.preferredWidth: 10
                            Layout.preferredHeight: 10
                            Layout.leftMargin: 4
                            Layout.rightMargin: 4
                            source: "arrow-right"
                            color: Theme.subtext
                            isMask: true
                        }
                        Rectangle {
                            Layout.preferredWidth: crumbText.implicitWidth + 12
                            Layout.preferredHeight: 26
                            radius: 4
                            color: crumbHover.hovered && modelData.location !== "" ? Theme.hover : "transparent"
                            Text {
                                id: crumbText
                                anchors.centerIn: parent
                                text: modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.fontSize
                            }
                            HoverHandler { id: crumbHover }
                            TapHandler {
                                onTapped: if (modelData.location !== "") bar.tab.navigate(modelData.location)
                            }
                        }
                    }
                }
                // Empty part: type a path.
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    TapHandler { onTapped: bar.editAddress() }
                    HoverHandler { cursorShape: Qt.IBeamCursor }
                }
                IconButton {
                    Layout.preferredHeight: 26
                    icon: "view-refresh"
                    tooltip: backend.text("refresh") + " (F5)"
                    onClicked: bar.tab.refresh()
                }
            }

            TextInput {
                id: pathInput
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                verticalAlignment: TextInput.AlignVCenter
                visible: bar.editing
                color: Theme.text
                selectionColor: Theme.accent
                selectedTextColor: "#FFFFFF"
                font.pixelSize: Theme.fontSize
                clip: true
                onAccepted: {
                    bar.editing = false;
                    backend.enterAddress(text);      // a path, a place or "cmd"
                }
                Keys.onEscapePressed: bar.editing = false
                onActiveFocusChanged: if (!activeFocus) bar.editing = false
            }
        }

        // Search box
        Rectangle {
            Layout.preferredWidth: Math.min(320, bar.width * 0.26)
            Layout.preferredHeight: 34
            Layout.leftMargin: 8
            radius: 4
            color: Theme.field
            border.width: 1
            border.color: searchInput.activeFocus ? Theme.accent : Theme.fieldBorder

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 6
                spacing: 8
                Kirigami.Icon {
                    Layout.preferredWidth: 14
                    Layout.preferredHeight: 14
                    source: "search"
                    color: Theme.subtext
                    isMask: true
                }
                TextInput {
                    id: searchInput
                    Layout.fillWidth: true
                    color: Theme.text
                    selectionColor: Theme.accent
                    selectedTextColor: "#FFFFFF"
                    font.pixelSize: Theme.fontSize
                    clip: true
                    Accessible.role: Accessible.EditableText
                    Accessible.name: placeholder.text
                    onTextEdited: searchDelay.restart()
                    onAccepted: {
                        searchDelay.stop();
                        bar.tab.search(text);
                    }
                    Keys.onEscapePressed: {
                        text = "";
                        bar.tab.search("");
                    }
                    Text {
                        id: placeholder
                        anchors.verticalCenter: parent.verticalCenter
                        visible: searchInput.text === ""
                        text: backend.format("search_in", "name", bar.tab.title)
                        color: Theme.subtext
                        font.pixelSize: Theme.fontSize
                        elide: Text.ElideRight
                        width: searchInput.width
                    }
                }
                IconButton {
                    visible: searchInput.text !== ""
                    Layout.preferredHeight: 24
                    Layout.preferredWidth: 24
                    icon: "edit-clear"
                    iconSize: 12
                    onClicked: {
                        searchInput.text = "";
                        bar.tab.search("");
                    }
                }
            }
            Timer {
                id: searchDelay
                interval: 500
                onTriggered: bar.tab.search(searchInput.text)
            }
        }
    }

    WinMenu {
        id: recentMenu
        items: bar.tab.recentLocations.map(l => ({ text: l.name, icon: l.icon, action: l.location }))
        onTriggered: location => bar.tab.navigate(location)
    }
}
