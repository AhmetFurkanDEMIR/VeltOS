/*
    VeltOS Maps: Google Maps over the whole window, as Windows 11's Maps
    showed its map, with VeltOS' own controls floating at the right edge
    (My location, location access, default location, Location settings),
    messages as Windows 11 InfoBars, a loading line at the top and an
    offline page. Google's own search box and buttons stay where Google
    draws them; there is no second search box. Location is opt-in.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
import org.kde.kirigami as Kirigami
import "."

ApplicationWindow {
    id: window

    width: 1280
    height: 820
    minimumWidth: 640
    minimumHeight: 480
    visible: true
    title: backend.appTitle
    color: Theme.window

    property bool loadFailed: false

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
        function onRaiseRequested() {
            if (window.visibility === Window.Minimized)
                window.showNormal();
            window.raise();
            window.requestActivate();
        }
    }

    // A round floating button of the right-hand column.
    component MapButton: Rectangle {
        id: mapButton
        property string iconName
        property string tip
        property bool on: false
        property bool enabledState: true
        signal clicked()

        width: 44
        height: 44
        radius: 8
        opacity: enabledState ? 1 : 0.5
        color: on ? Theme.accent : (press.pressed ? Theme.cardPressed : hover.hovered ? Theme.cardHover : Theme.card)
        border.width: on ? 0 : 1
        border.color: Theme.cardBorder
        Accessible.role: Accessible.Button
        Accessible.name: tip
        Accessible.checked: on
        Behavior on color { ColorAnimation { duration: 120 } }

        Kirigami.Icon {
            anchors.centerIn: parent
            width: 20
            height: 20
            source: mapButton.iconName
            isMask: true
            color: mapButton.on ? "white" : Theme.text
        }
        HoverHandler { id: hover; enabled: mapButton.enabledState; cursorShape: Qt.PointingHandCursor }
        TapHandler {
            id: press
            enabled: mapButton.enabledState
            gesturePolicy: TapHandler.ReleaseWithinBounds
            onTapped: mapButton.clicked()
        }
        ToolTip.visible: hover.hovered
        ToolTip.delay: 500
        ToolTip.text: tip
    }

    // A Windows 11 InfoBar: coloured edge and icon, title, message, actions.
    component InfoBar: Rectangle {
        id: bar
        property string kind: "info"          // info, progress, error
        property string heading
        property string message
        property bool closable: true
        default property alias actions: actionRow.data
        signal closed()

        width: Math.min(window.width - 120, 680)
        implicitHeight: barRow.implicitHeight + 24
        radius: 8
        color: kind === "error" ? Theme.errorSoft : Theme.card
        border.width: 1
        border.color: Theme.cardBorder

        RowLayout {
            id: barRow
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 16
            anchors.rightMargin: 8
            spacing: 12

            Item {
                Layout.preferredWidth: 20
                Layout.preferredHeight: 20
                BusyIndicator {
                    anchors.centerIn: parent
                    width: 24
                    height: 24
                    visible: bar.kind === "progress"
                    running: visible
                }
                Rectangle {
                    anchors.fill: parent
                    visible: bar.kind !== "progress"
                    radius: 10
                    color: bar.kind === "error" ? Theme.error : Theme.accent
                    Label {
                        anchors.centerIn: parent
                        text: bar.kind === "error" ? "!" : "i"
                        color: "white"
                        font.pixelSize: 13
                        font.weight: Font.Bold
                    }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    Layout.fillWidth: true
                    visible: bar.heading !== ""
                    text: bar.heading
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
                Label {
                    Layout.fillWidth: true
                    text: bar.message
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.WordWrap
                }
            }
            RowLayout {
                id: actionRow
                spacing: 8
            }
            // Windows 11's InfoBar close: a plain rectangle, only shaded on
            // hover (the rounded one looked oval; product owner, 2026-10-26).
            MapButton {
                id: barClose
                objectName: "infoBarClose"
                visible: bar.closable
                width: 40
                height: 32
                radius: 4
                color: closeHover.hovered ? Theme.cardHover : "transparent"
                border.width: 0
                HoverHandler { id: closeHover }
                iconName: "window-close-symbolic"
                tip: backend.text("close")
                onClicked: bar.closed()
            }
        }
    }

    component TextButton: Rectangle {
        id: textButton
        property string text
        property bool primary: false
        signal clicked()
        implicitWidth: buttonLabel.implicitWidth + 28
        implicitHeight: 32
        radius: 5
        color: primary ? (buttonTap.pressed ? Qt.darker(Theme.accent, 1.15) : buttonHover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                       : (buttonTap.pressed ? Theme.cardPressed : buttonHover.hovered ? Theme.cardHover : Theme.card)
        border.width: primary ? 0 : 1
        border.color: Theme.cardBorder
        Accessible.role: Accessible.Button
        Accessible.name: text
        Label {
            id: buttonLabel
            anchors.centerIn: parent
            text: textButton.text
            color: textButton.primary ? "white" : Theme.text
            font.pixelSize: Theme.bodySize
        }
        HoverHandler { id: buttonHover; cursorShape: Qt.PointingHandCursor }
        TapHandler { id: buttonTap; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: textButton.clicked() }
    }

    WebEngineView {
        id: map
        objectName: "mapView"
        anchors.fill: parent
        url: backend.mapUrl
        backgroundColor: Theme.window
        settings.javascriptEnabled: true
        settings.javascriptCanOpenWindows: false
        settings.pluginsEnabled: false
        settings.localContentCanAccessRemoteUrls: false
        settings.localContentCanAccessFileUrls: false
        // Google's pages in the app's language; cookies kept in Maps' own
        // profile, so Google's consent and sign-in are remembered as in a
        // browser (VeltOS Maps' data only, nothing shared with Firefox).
        profile: WebEngineProfile {
            storageName: "veltos-maps"
            offTheRecord: false
            httpAcceptLanguage: backend.acceptLanguage
            persistentCookiesPolicy: WebEngineProfile.AllowPersistentCookies
        }

        onLoadingChanged: request => {
            if (request.status === WebEngineLoadingInfo.LoadFailedStatus
                    && request.errorDomain !== WebEngineLoadingInfo.NoErrorDomain
                    && request.errorCode !== -3)          // -3: aborted by a newer load
                window.loadFailed = true;
            else if (request.status === WebEngineLoadingInfo.LoadSucceededStatus)
                window.loadFailed = false;
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

    // The loading line at the top, in the accent colour.
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        height: 3
        width: parent.width * map.loadProgress / 100
        color: Theme.accent
        visible: map.loading && !window.loadFailed
        Behavior on width { NumberAnimation { duration: 150 } }
    }

    // Offline: Windows 11's "can't reach" page with Try again.
    Rectangle {
        anchors.fill: parent
        visible: window.loadFailed
        color: Theme.window
        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 80, 460)
            spacing: 12
            Image {
                Layout.alignment: Qt.AlignHCenter
                source: "icons/brand.svg"
                sourceSize.width: 72
                sourceSize.height: 72
                opacity: 0.6
            }
            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: backend.text("offline_title")
                color: Theme.text
                font.pixelSize: Theme.bodySize + 8
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: backend.text("offline_desc")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
            TextButton {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 8
                primary: true
                text: backend.text("retry")
                onClicked: {
                    window.loadFailed = false;
                    map.reload();
                }
            }
        }
    }

    // VeltOS' controls, floating at the right edge in the middle (Google's
    // own buttons sit in the corners).
    Column {
        anchors.right: parent.right
        anchors.rightMargin: 14
        anchors.verticalCenter: parent.verticalCenter
        spacing: 8
        visible: !window.loadFailed

        MapButton {
            objectName: "currentLocationButton"
            iconName: "mark-location-symbolic"
            tip: backend.locationEnabled ? backend.text("my_location") : backend.text("location_disabled")
            enabledState: backend.locationEnabled
            enabled: backend.locationEnabled
            onClicked: backend.requestCurrentLocation()
        }
        MapButton {
            objectName: "locationButton"
            iconName: backend.locationEnabled ? "find-location-symbolic" : "location-services-disabled-symbolic"
            on: backend.locationEnabled
            tip: backend.text(backend.locationEnabled ? "location_on_tip" : "location_off_tip")
            onClicked: backend.setLocationEnabled(!backend.locationEnabled)
        }
        MapButton {
            iconName: "go-home-symbolic"
            tip: backend.hasDefaultLocation ? backend.text("show_default") : backend.text("set_default_title")
            onClicked: backend.hasDefaultLocation ? backend.showDefaultLocation() : backend.startSettingDefault()
        }
        MapButton {
            iconName: "configure-symbolic"
            tip: backend.text("settings")
            onClicked: backend.openLocationSettings()
        }
    }

    // Messages at the bottom, above Google's attribution line.
    Column {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 44
        spacing: 8

        InfoBar {
            objectName: "setDefaultBar"
            visible: backend.settingDefault
            heading: backend.text("set_default_title")
            message: backend.text("set_default_desc")
            onClosed: backend.cancelSettingDefault()
            TextButton {
                primary: true
                text: backend.text("set_default_button")
                onClicked: backend.saveDefaultFromView(map.url.toString())
            }
        }
        InfoBar {
            objectName: "statusBar"
            visible: backend.status !== ""
            kind: backend.statusKind || "info"
            message: backend.status
            onClosed: backend.clearStatus()
        }
        InfoBar {
            objectName: "privacyBar"
            visible: backend.privacyNoteVisible && !window.loadFailed
            message: backend.text("privacy_note")
            closable: false
            TextButton {
                text: backend.text("got_it")
                onClicked: backend.dismissPrivacyNote()
            }
        }
    }

    // Information goes away by itself; errors stay until closed.
    Timer {
        interval: 6000
        running: backend.status !== "" && backend.statusKind === "info"
        onTriggered: backend.clearStatus()
    }
}
