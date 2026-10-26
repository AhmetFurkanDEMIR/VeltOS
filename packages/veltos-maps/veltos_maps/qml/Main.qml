/*
    VeltOS Maps: Google Maps in a VeltOS window. Location is opt-in and the
    web profile is private to this process.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
import "."

ApplicationWindow {
    id: window

    width: 1280
    height: 820
    minimumWidth: 760
    minimumHeight: 520
    visible: true
    title: backend.appTitle
    color: Theme.window

    function updateLocationPermissions() {
        const permissions = map.profile.listPermissionsForPermissionType(WebEnginePermission.Geolocation);
        for (const permission of permissions) {
            if (backend.isGoogleMapsUrl(permission.origin.toString())) {
                if (backend.locationEnabled)
                    permission.reset();
                else
                    permission.deny();
            }
        }
    }

    Connections {
        target: backend
        function onLocationChanged() { window.updateLocationPermissions(); }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 62
            color: Theme.window
            border.width: 1
            border.color: Theme.cardBorder

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 22
                spacing: 12

                Image {
                    source: "icons/brand.svg"
                    sourceSize.width: 32
                    sourceSize.height: 32
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                }
                Label {
                    text: backend.appTitle
                    color: Theme.text
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }
                Item { Layout.preferredWidth: 12 }

                TextField {
                    id: placeSearch
                    objectName: "placeSearch"
                    Layout.preferredWidth: Math.min(420, window.width * 0.38)
                    Layout.preferredHeight: 38
                    placeholderText: backend.text("search_placeholder")
                    selectByMouse: true
                    onAccepted: backend.search(text)
                    background: Rectangle {
                        radius: 6
                        color: Theme.field
                        border.width: placeSearch.activeFocus ? 2 : 1
                        border.color: placeSearch.activeFocus ? Theme.accent : Theme.fieldBorder
                    }
                }
                Button {
                    text: backend.text("search")
                    onClicked: backend.search(placeSearch.text)
                }
                Button {
                    objectName: "currentLocationButton"
                    text: backend.text("my_location")
                    enabled: backend.locationEnabled
                    onClicked: backend.requestCurrentLocation()
                }
                Item { Layout.fillWidth: true }
                Button {
                    id: locationButton
                    text: backend.text(backend.locationEnabled ? "location_on" : "location_off")
                    checkable: true
                    checked: backend.locationEnabled
                    Accessible.name: backend.text("location_hint")
                    onClicked: backend.setLocationEnabled(!backend.locationEnabled)
                }
                Button {
                    text: backend.text("settings")
                    onClicked: backend.openLocationSettings()
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: backend.status === "" ? 30 : 38
            color: Theme.accentSoft
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 22
                Label {
                    Layout.fillWidth: true
                    text: backend.status !== "" ? backend.status : backend.text("privacy_note")
                    color: Theme.subtext
                    font.pixelSize: Theme.captionSize
                    elide: Text.ElideRight
                }
                Label {
                    text: backend.text(backend.locationEnabled ? "location_on" : "location_off")
                    color: backend.locationEnabled ? Theme.accent : Theme.subtext
                    font.pixelSize: Theme.captionSize
                }
            }
        }

        WebEngineView {
            id: map
            objectName: "mapView"
            Layout.fillWidth: true
            Layout.fillHeight: true
            url: backend.mapUrl
            backgroundColor: Theme.window
            settings.javascriptEnabled: true
            settings.javascriptCanOpenWindows: false
            settings.pluginsEnabled: false
            settings.localContentCanAccessRemoteUrls: false
            settings.localContentCanAccessFileUrls: false
            profile: WebEngineProfile {
                httpCacheType: WebEngineProfile.MemoryHttpCache
                persistentCookiesPolicy: WebEngineProfile.NoPersistentCookies
            }

            onPermissionRequested: permission => {
                if (permission.permissionType === WebEnginePermission.Geolocation
                        && backend.canShareLocation(permission.origin.toString())) {
                    permission.grant();
                } else {
                    permission.deny();
                }
            }
            onNavigationRequested: request => {
                const target = request.url.toString();
                if (backend.isGoogleMapsUrl(target))
                    return;
                request.action = WebEngineNavigationRequest.IgnoreRequest;
                if (request.navigationType === WebEngineNavigationRequest.LinkClickedNavigation)
                    backend.openExternal(target);
            }
            onNewWindowRequested: request => {
                const target = request.requestedUrl.toString();
                if (backend.isGoogleMapsUrl(target))
                    map.url = request.requestedUrl;
                else
                    backend.openExternal(target);
            }
        }
    }
}
