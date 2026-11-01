// Accounts > Sign-in options: change the password (current, new,
// confirm and a hint, like Windows), the password reset USB, and whether
// waking up asks for it.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    property bool expanded: false
    property bool busy: false
    property string result: ""        // "", "ok" or an error text key
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: {
        backend.refreshPrefs();
        backend.refreshResetUsb();
    }
    property bool choosing: false
    property string chosenDrive: ""

    Connections {
        target: backend
        function onAccountResult(operation, error) {
            if (operation !== "password")
                return;
            page.busy = false;
            page.result = error === "" ? "ok" : error;
            if (error === "") {
                current.text = "";
                fresh.text = "";
                confirm.text = "";
                page.expanded = false;
            }
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "dialog-password-symbolic"
        title: backend.text("password")
        description: backend.text("password_desc")
        clickable: true
        onClicked: page.expanded = !page.expanded
        VButton {
            text: backend.text("change")
            onClicked: page.expanded = !page.expanded
        }
    }
    Card {
        Layout.fillWidth: true
        visible: page.expanded
        ColumnLayout {
            width: parent.width
            spacing: 8
            Label { text: backend.text("change_password"); color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
            Label { text: backend.text("current_password"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: current; Layout.preferredWidth: 320; password: true }
            Label { text: backend.text("new_password"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: fresh; Layout.preferredWidth: 320; password: true }
            Label { text: backend.text("confirm_password"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: confirm; Layout.preferredWidth: 320; password: true; onAccepted: change.clicked() }
            Label { text: backend.text("password_hint"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: hintField; objectName: "hintField"; Layout.preferredWidth: 320; text: backend.resetUsb.hint || "" }
            Label {
                Layout.fillWidth: true
                text: backend.text("password_hint_note")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.topMargin: 6
                spacing: 8
                VButton {
                    id: change
                    primary: true
                    text: page.busy ? backend.text("loading") : backend.text("change")
                    enabledState: !page.busy && current.text.length > 0 && fresh.text.length > 0
                    onClicked: {
                        page.busy = true;
                        page.result = "";
                        backend.changePasswordWithHint(current.text, fresh.text, confirm.text, hintField.text);
                    }
                }
                VButton {
                    text: backend.text("cancel")
                    onClicked: page.expanded = false
                }
            }
        }
    }
    Label {
        Layout.fillWidth: true
        visible: page.result !== ""
        text: page.result === "ok" ? backend.text("password_changed") : (page.result ? backend.text(page.result) : "")
        color: page.result === "ok" ? Theme.text : Theme.danger
        font.pixelSize: Theme.bodySize
        wrapMode: Text.WordWrap
    }
    // Password reset USB (veltos-auth's password-recovery): shown only
    // where it can be made; without one VeltOS says plainly that a
    // forgotten password cannot be reset.
    SettingRow {
        Layout.fillWidth: true
        Layout.topMargin: 14
        visible: backend.resetUsb.available === true
        icon: "drive-removable-media-usb-pendrive-symbolic"
        title: backend.text("reset_usb")
        description: backend.resetUsb.configured ? backend.text("reset_usb_on") : backend.text("reset_usb_off")
        RowLayout {
            spacing: 8
            VButton {
                text: backend.resetUsb.configured ? backend.text("reset_usb_again") : backend.text("reset_usb_create")
                enabledState: backend.resetUsb.busy !== true
                onClicked: {
                    page.choosing = !page.choosing;
                    if (page.choosing)
                        backend.refreshResetUsb();
                }
            }
            VButton {
                visible: backend.resetUsb.configured === true
                text: backend.text("reset_usb_remove")
                enabledState: backend.resetUsb.busy !== true
                onClicked: backend.removeResetUsb()
            }
        }
    }
    Card {
        Layout.fillWidth: true
        visible: page.choosing && backend.resetUsb.available === true
        ColumnLayout {
            width: parent.width
            spacing: 8
            Label {
                Layout.fillWidth: true
                text: backend.text("reset_usb_choose")
                color: Theme.text
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
            Repeater {
                model: backend.resetUsb.drives || []
                delegate: Rectangle {
                    id: driveRow
                    required property var modelData
                    readonly property bool chosen: page.chosenDrive === modelData.path
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    radius: 6
                    color: chosen ? Theme.navSelected : (rowHover.hovered ? Theme.navHover : "transparent")
                    border.width: chosen ? 1 : 0
                    border.color: Theme.accent
                    Accessible.role: Accessible.RadioButton
                    Accessible.name: driveName.text
                    Accessible.checked: chosen
                    Label {
                        id: driveName
                        anchors.verticalCenter: parent.verticalCenter
                        x: 12
                        width: parent.width - 24
                        elide: Text.ElideRight
                        text: (driveRow.modelData.label || driveRow.modelData.model || "USB") + " ("
                              + Math.round(driveRow.modelData.size / 1e8) / 10 + " GB) · " + driveRow.modelData.path
                        color: Theme.text
                        font.pixelSize: Theme.bodySize
                    }
                    HoverHandler { id: rowHover }
                    TapHandler {
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onTapped: page.chosenDrive = driveRow.modelData.path
                    }
                }
            }
            Label {
                visible: (backend.resetUsb.drives || []).length === 0
                text: backend.text("reset_usb_none")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
            }
            RowLayout {
                spacing: 8
                VButton {
                    primary: true
                    text: backend.resetUsb.busy ? backend.text("loading") : backend.text("reset_usb_create")
                    enabledState: backend.resetUsb.busy !== true
                                  && (backend.resetUsb.drives || []).some(d => d.path === page.chosenDrive)
                    onClicked: backend.createResetUsb(page.chosenDrive)
                }
                VButton {
                    text: backend.text("reset_usb_refresh")
                    onClicked: backend.refreshResetUsb()
                }
                VButton {
                    text: backend.text("cancel")
                    onClicked: page.choosing = false
                }
            }
        }
    }
    Label {
        Layout.fillWidth: true
        visible: backend.resetUsb.error !== undefined && (backend.resetUsb.error !== "" || backend.resetUsb.created === true)
        text: backend.resetUsb.created === true ? backend.text("reset_usb_made")
              : backend.resetUsb.error === "not-allowed" ? backend.text("reset_usb_not-allowed")
              : backend.text("reset_usb_error")
        color: backend.resetUsb.created === true ? Theme.text : Theme.danger
        font.pixelSize: Theme.bodySize
        wrapMode: Text.WordWrap
    }
    Connections {
        target: backend
        function onResetUsbChanged() {
            if (backend.resetUsb.created === true)
                page.choosing = false;
        }
    }
    SettingRow {
        Layout.fillWidth: true
        Layout.topMargin: 14
        icon: "system-lock-screen-symbolic"
        title: backend.text("lock_on_resume")
        ToggleSwitch {
            checked: backend.prefs.lockOnResume !== false
            enabledState: backend.prefs.loaded === true
            accessibleName: backend.text("lock_on_resume")
            onToggled: on => backend.setPref("lockOnResume", on)
        }
    }
}
