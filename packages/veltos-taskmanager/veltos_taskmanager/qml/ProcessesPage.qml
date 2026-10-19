// Processes: like Windows 11 - the totals over the CPU and Memory columns,
// apps / background processes / system processes, busy cells coloured,
// "End task" for the selected row (also Delete and the context menu).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: page
    spacing: 0

    property string selectedKey: ""
    property string selectedName: ""
    readonly property int nameWidth: Math.max(240, width - 2 * columnWidth - 32)
    readonly property int columnWidth: 110

    function endSelected() {
        if (selectedKey !== "") {
            backend.endTask(selectedKey);
            selectedKey = "";
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.margins: 16
        spacing: 8
        Label {
            Layout.fillWidth: true
            text: backend.texts.processes
            font.pixelSize: Theme.pageTitleSize
            font.weight: Font.DemiBold
            color: Theme.text
        }
        TextField {
            id: search
            Layout.preferredWidth: 260
            placeholderText: backend.texts.search
            onTextChanged: backend.setSearch(text)
        }
        Button {
            text: backend.texts.run_task
            icon.name: "system-run-symbolic"
            flat: true
            onClicked: backend.runNewTask()
        }
        Button {
            text: backend.texts.end_task
            icon.name: "process-stop-symbolic"
            flat: true
            enabled: page.selectedKey !== ""
            onClicked: page.endSelected()
        }
    }

    // Column headings: totals above the names, as on Windows.
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 48
        color: "transparent"
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 0
            Label {
                Layout.preferredWidth: page.nameWidth
                Layout.alignment: Qt.AlignBottom
                bottomPadding: 6
                text: backend.texts.name
                color: Theme.subtext
            }
            Repeater {
                model: [[backend.totals.cpu, backend.texts.cpu], [backend.totals.memory, backend.texts.memory]]
                ColumnLayout {
                    required property var modelData
                    Layout.preferredWidth: page.columnWidth
                    spacing: 0
                    Label {
                        Layout.alignment: Qt.AlignRight
                        rightPadding: 8
                        text: modelData[0]
                        font.pixelSize: 16
                        color: Theme.text
                    }
                    Label {
                        Layout.alignment: Qt.AlignRight
                        rightPadding: 8
                        text: modelData[1]
                        color: Theme.subtext
                    }
                }
            }
        }
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 1
            color: Theme.cardBorder
        }
    }

    ListView {
        id: list
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        focus: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}
        Keys.onDeletePressed: page.endSelected()

        model: backend.rows
        delegate: MouseArea {
            id: row
            required property string kind
            required property string key
            required property var name
            required property var icon
            required property var count
            required property var cpu
            required property var cpuText
            required property var memoryText
            required property var memoryShare
            required property var title
            readonly property bool header: kind === "header"

            width: ListView.view.width
            height: header ? 40 : 34
            hoverEnabled: !header
            enabled: !header
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onPressed: {
                page.selectedKey = key;
                page.selectedName = name;
                list.forceActiveFocus();
            }
            onClicked: mouse => {
                if (mouse.button === Qt.RightButton) {
                    menu.popup();
                }
            }

            // Group heading: "Apps (3)".
            Label {
                visible: row.header
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.leftMargin: 16
                anchors.bottomMargin: 6
                text: row.title || ""
                font.weight: Font.DemiBold
                color: Theme.text
            }

            Rectangle {
                visible: !row.header
                anchors.fill: parent
                anchors.leftMargin: 6
                anchors.rightMargin: 6
                radius: 4
                color: page.selectedKey === row.key ? Theme.rowSelected
                     : (row.containsMouse ? Theme.rowHover : "transparent")
            }
            RowLayout {
                visible: !row.header
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 0
                RowLayout {
                    Layout.preferredWidth: page.nameWidth
                    spacing: 10
                    Kirigami.Icon {
                        implicitWidth: 20
                        implicitHeight: 20
                        source: row.icon || ""
                    }
                    Label {
                        Layout.fillWidth: true
                        text: (row.count || 0) > 1 ? row.name + " (" + row.count + ")" : (row.name || "")
                        elide: Text.ElideRight
                        color: Theme.text
                    }
                }
                Rectangle {
                    Layout.preferredWidth: page.columnWidth
                    Layout.fillHeight: true
                    color: Theme.heat(row.cpu || 0)
                    Label {
                        anchors.right: parent.right
                        anchors.rightMargin: 8
                        anchors.verticalCenter: parent.verticalCenter
                        text: row.cpuText || ""
                        color: Theme.text
                    }
                }
                Rectangle {
                    Layout.preferredWidth: page.columnWidth
                    Layout.fillHeight: true
                    color: Theme.heat((row.memoryShare || 0) * 4)
                    Label {
                        anchors.right: parent.right
                        anchors.rightMargin: 8
                        anchors.verticalCenter: parent.verticalCenter
                        text: row.memoryText || ""
                        color: Theme.text
                    }
                }
            }
        }
    }

    Menu {
        id: menu
        MenuItem {
            text: backend.texts.end_task
            onTriggered: page.endSelected()
        }
    }
}
