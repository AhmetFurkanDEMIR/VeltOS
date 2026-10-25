/*
    VeltOS Weather in the layout of Windows 11's Weather app: a narrow
    navigation rail (Forecast, Historical weather, Favorites, Settings), a
    search box for places, the place with its star and home buttons, and
    one page at a time. `backend` (app.py) gets the weather from
    Open-Meteo and turns it into texts in the chosen units.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ApplicationWindow {
    id: window

    width: 1220
    height: 820
    minimumWidth: 720
    minimumHeight: 520
    visible: true
    title: backend.text("app_title")
    color: Theme.window

    readonly property var pages: ["forecast", "history", "favorites"]

    component RailButton: Rectangle {
        id: rail
        property string page
        property string glyph
        readonly property bool chosen: backend.page === page
        Layout.preferredWidth: 44
        Layout.preferredHeight: 40
        Layout.alignment: Qt.AlignHCenter
        radius: 5
        color: chosen ? Theme.navSelected : (railHover.hovered ? Theme.navHover : "transparent")
        Accessible.role: Accessible.PageTab
        Accessible.name: backend.text(page)
        Rectangle {
            visible: rail.chosen
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: 3
            height: 16
            radius: 1.5
            color: Theme.accent
        }
        Glyph {
            anchors.centerIn: parent
            name: rail.glyph
            width: 20
            height: 20
            tint: rail.chosen ? Theme.accent : Theme.text
        }
        HoverHandler { id: railHover }
        TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: backend.setPage(rail.page) }
        ToolTip.visible: railHover.hovered
        ToolTip.delay: 500
        ToolTip.text: backend.text(page)
    }

    component IconButton: Rectangle {
        id: iconButton
        property string glyph
        property string tip
        property bool checked: false
        signal clicked()
        implicitWidth: 36
        implicitHeight: 36
        radius: 5
        color: iconHover.hovered ? Theme.navHover : "transparent"
        Accessible.role: Accessible.Button
        Accessible.name: tip
        Glyph {
            anchors.centerIn: parent
            name: iconButton.glyph
            width: 18
            height: 18
            tint: iconButton.checked ? Theme.accent : Theme.text
        }
        HoverHandler { id: iconHover }
        TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: iconButton.clicked() }
        ToolTip.visible: iconHover.hovered && tip !== ""
        ToolTip.delay: 500
        ToolTip.text: tip
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // --- navigation rail ------------------------------------------------------------------------
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 60
            color: Theme.rail
            ColumnLayout {
                anchors.fill: parent
                anchors.topMargin: 12
                anchors.bottomMargin: 12
                spacing: 4
                RailButton { page: "forecast"; glyph: "forecast" }
                RailButton { page: "history"; glyph: "history" }
                RailButton { page: "favorites"; glyph: "favorites" }
                Item { Layout.fillHeight: true }
                RailButton { page: "settings"; glyph: "settings" }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // --- search and the place ---------------------------------------------------------------
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 20
                Layout.rightMargin: 20
                Layout.topMargin: 12
                spacing: 10

                Rectangle {
                    id: searchBox
                    Layout.preferredWidth: Math.min(380, window.width * 0.36)
                    Layout.preferredHeight: 34
                    radius: 5
                    color: Theme.field
                    border.width: 1
                    border.color: searchField.activeFocus ? Theme.accent : Theme.fieldBorder
                    Rectangle {
                        visible: searchField.activeFocus
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 1
                        height: 2
                        color: Theme.accent
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 6
                        spacing: 8
                        TextInput {
                            id: searchField
                            objectName: "search"
                            Layout.fillWidth: true
                            color: Theme.text
                            font.pixelSize: Theme.bodySize
                            selectByMouse: true
                            clip: true
                            selectionColor: Theme.accent
                            onTextEdited: searchDelay.restart()
                            Keys.onDownPressed: if (results.visible) resultList.incrementCurrentIndex()
                            Keys.onUpPressed: if (results.visible) resultList.decrementCurrentIndex()
                            Keys.onEscapePressed: { text = ""; backend.search(""); }
                            onAccepted: {
                                if (backend.searchResults.length > 0)
                                    window.choose(Math.max(0, resultList.currentIndex));
                            }
                            Text {
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                                visible: searchField.text === ""
                                text: backend.text("search")
                                color: Theme.faint
                                font.pixelSize: Theme.bodySize
                            }
                        }
                        Glyph { name: "search"; tint: Theme.subtext }
                    }
                    Timer {
                        id: searchDelay
                        interval: 300
                        onTriggered: backend.search(searchField.text)
                    }
                    Accessible.role: Accessible.EditableText
                    Accessible.name: backend.text("search")
                }

                Item { Layout.fillWidth: true }

                Text {
                    visible: backend.loading
                    text: backend.text("loading")
                    color: Theme.subtext
                    font.pixelSize: Theme.captionSize
                }
                IconButton {
                    objectName: "refresh"
                    glyph: "refresh"
                    tip: backend.text("refresh")
                    onClicked: backend.refresh()
                }
                // °F / °C, as Windows 11 Weather shows it in its header.
                Rectangle {
                    Layout.preferredHeight: 32
                    Layout.preferredWidth: unitRow.implicitWidth + 8
                    radius: 5
                    color: Theme.card
                    border.width: 1
                    border.color: Theme.cardBorder
                    Row {
                        id: unitRow
                        anchors.centerIn: parent
                        spacing: 2
                        Repeater {
                            model: ["F", "C"]
                            delegate: Rectangle {
                                id: unitChip
                                required property string modelData
                                width: 38
                                height: 26
                                radius: 4
                                color: backend.unitName === modelData ? Theme.accent : (unitHover.hovered ? Theme.navHover : "transparent")
                                Text {
                                    anchors.centerIn: parent
                                    text: "°" + unitChip.modelData
                                    color: backend.unitName === unitChip.modelData ? "#FFFFFF" : Theme.text
                                    font.pixelSize: Theme.bodySize
                                }
                                HoverHandler { id: unitHover }
                                TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: backend.setUnit(unitChip.modelData) }
                            }
                        }
                    }
                }
            }

            RowLayout {
                visible: backend.hasPlace && (backend.page === "forecast" || backend.page === "history")
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 20
                Layout.topMargin: 12
                spacing: 6
                Glyph { name: "pin"; tint: Theme.text; width: 20; height: 20 }
                Text {
                    objectName: "placeName"
                    text: backend.placeName
                    color: Theme.text
                    font.pixelSize: Theme.headingSize + 4
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.leftMargin: 4
                    text: backend.placeRegion
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    Layout.alignment: Qt.AlignBottom
                    bottomPadding: 4
                    elide: Text.ElideRight
                    Layout.maximumWidth: 360
                }
                IconButton {
                    objectName: "favoriteButton"
                    glyph: backend.isFavorite ? "star-filled" : "star"
                    checked: backend.isFavorite
                    tip: backend.isFavorite ? backend.text("remove_favorite") : backend.text("add_favorite")
                    onClicked: backend.toggleFavorite()
                }
                IconButton {
                    glyph: "home"
                    checked: backend.isHome
                    tip: backend.isHome ? backend.text("home") : backend.text("set_home")
                    onClicked: backend.setHome()
                }
                Item { Layout.fillWidth: true }
            }

            // --- can't connect ------------------------------------------------------------------------
            Rectangle {
                objectName: "offlineBar"
                visible: backend.offline && !backend.loading
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                Layout.topMargin: 10
                Layout.preferredHeight: 44
                radius: 5
                color: Theme.warning
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 8
                    Text {
                        Layout.fillWidth: true
                        text: backend.text("offline") + (backend.hasForecast ? " " + backend.text("showing_saved") : "")
                        color: Theme.warningText
                        font.pixelSize: Theme.bodySize
                        elide: Text.ElideRight
                    }
                    VButton { text: backend.text("try_again"); onClicked: backend.refresh() }
                }
            }

            // --- pages ----------------------------------------------------------------------------------
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.topMargin: 12

                // No place yet: ask for one.
                ColumnLayout {
                    objectName: "firstPlace"
                    visible: !backend.hasPlace && backend.page !== "settings" && backend.page !== "favorites"
                    anchors.centerIn: parent
                    spacing: 12
                    WeatherIcon {
                        Layout.alignment: Qt.AlignHCenter
                        name: "partly-cloudy-day"
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 120
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: backend.loading ? backend.text("loading") : backend.text("first_place")
                        color: Theme.text
                        font.pixelSize: Theme.subtitleSize
                    }
                }

                StackLayout {
                    anchors.fill: parent
                    visible: backend.hasPlace || backend.page === "settings" || backend.page === "favorites"
                    currentIndex: ["forecast", "history", "favorites", "settings"].indexOf(backend.page)
                    ForecastPage { objectName: "forecastPage" }
                    HistoryPage { objectName: "historyPage" }
                    FavoritesPage { objectName: "favoritesPage" }
                    SettingsPage { objectName: "settingsPage" }
                }
            }
        }
    }

    // --- search results ---------------------------------------------------------------------------------
    function choose(index) {
        searchField.text = "";
        searchField.focus = false;
        backend.choosePlace(index);
    }

    Popup {
        id: results
        objectName: "searchResults"
        x: searchBox.mapToItem(window.contentItem, 0, 0).x
        y: searchBox.mapToItem(window.contentItem, 0, 0).y + searchBox.height + 4
        width: searchBox.width
        height: Math.min(360, Math.max(56, resultList.contentHeight + 12))
        padding: 6
        visible: searchField.activeFocus && searchField.text.length >= 2
                 && (backend.searchResults.length > 0 || !backend.searchBusy)
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        background: Rectangle {
            radius: Theme.radius
            color: Theme.menu
            border.width: 1
            border.color: Theme.cardBorder
        }
        ListView {
            id: resultList
            anchors.fill: parent
            clip: true
            model: backend.searchResults
            currentIndex: 0
            delegate: Rectangle {
                id: result
                required property var modelData
                required property int index
                width: ListView.view.width
                height: 48
                radius: 5
                color: ListView.isCurrentItem || resultHover.hovered ? Theme.navHover : "transparent"
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    spacing: 10
                    Glyph { name: "pin"; tint: Theme.subtext }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Text {
                            Layout.fillWidth: true
                            text: result.modelData.name
                            color: Theme.text
                            font.pixelSize: Theme.bodySize
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true
                            text: result.modelData.detail
                            color: Theme.subtext
                            font.pixelSize: Theme.captionSize
                            elide: Text.ElideRight
                        }
                    }
                }
                HoverHandler { id: resultHover }
                TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: window.choose(result.index) }
            }
            Text {
                anchors.centerIn: parent
                visible: resultList.count === 0
                text: backend.searchBusy ? backend.text("searching") : backend.text("no_results")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
            }
        }
    }
}
