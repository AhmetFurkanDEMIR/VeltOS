// VeltOS Task Manager window: navigation on the left (Processes,
// Performance, Startup apps), the page on the right - Windows 11 layout.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ApplicationWindow {
    id: window
    width: 1000
    height: 680
    minimumWidth: 720
    minimumHeight: 480
    visible: true
    title: backend.texts.app_title
    color: Theme.window

    property string page: "processes"

    readonly property var pages: [
        {"id": "processes", "icon": "view-list-details-symbolic", "text": backend.texts.processes},
        {"id": "performance", "icon": "office-chart-area-symbolic", "text": backend.texts.performance},
        {"id": "startup", "icon": "system-run-symbolic", "text": backend.texts.startup},
    ]

    // For tests: show a page by id.
    function showPage(id) {
        page = id;
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        ColumnLayout {
            Layout.preferredWidth: 220
            Layout.fillHeight: true
            Layout.topMargin: 8
            spacing: 2
            Repeater {
                model: window.pages
                MouseArea {
                    id: nav
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.leftMargin: 6
                    Layout.rightMargin: 6
                    Layout.preferredHeight: 38
                    hoverEnabled: true
                    onClicked: window.page = modelData.id
                    Accessible.name: modelData.text
                    Accessible.role: Accessible.PageTab

                    Rectangle {
                        anchors.fill: parent
                        radius: 4
                        color: window.page === nav.modelData.id ? Theme.navSelected
                             : (nav.containsMouse ? Theme.navHover : "transparent")
                    }
                    Rectangle {
                        visible: window.page === nav.modelData.id
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        width: 3
                        height: 16
                        radius: 1.5
                        color: Theme.accent
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        spacing: 14
                        Kirigami.Icon {
                            implicitWidth: 16
                            implicitHeight: 16
                            source: nav.modelData.icon
                            isMask: true
                            color: Theme.text
                        }
                        Label {
                            Layout.fillWidth: true
                            text: nav.modelData.text
                            color: Theme.text
                            elide: Text.ElideRight
                        }
                    }
                }
            }
            Item {
                Layout.fillHeight: true
            }
        }

        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            color: Theme.cardBorder
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: ["processes", "performance", "startup"].indexOf(window.page)
            ProcessesPage {}
            PerformancePage {}
            StartupPage {}
        }
    }
}
