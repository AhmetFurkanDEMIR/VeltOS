// Personalization > Lock screen (also Privacy & security > Screen lock):
// the lock screen's picture, lock automatically after a time, password on
// wake (kscreenlockerrc).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    readonly property var personal: backend.personal
    readonly property var wallpapers: personal.wallpapers || []
    readonly property string lockPath: personal.lockWallpaper ? personal.lockWallpaper
                                       : (wallpapers.length ? wallpapers[0].path : "")
    readonly property string previewSource: {
        for (const w of wallpapers) {
            if (w.path === lockPath)
                return "file://" + (Theme.dark ? w.previewDark : w.preview);
        }
        return lockPath !== "" ? "file://" + lockPath : "";
    }
    property date now: new Date()
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: {
        backend.refreshPrefs();
        backend.refreshPersonal();
    }

    Timer {
        interval: 20000
        running: page.visible
        repeat: true
        onTriggered: page.now = new Date()
    }

    // Preview: the lock screen with the chosen picture and its clock.
    Rectangle {
        Layout.alignment: Qt.AlignHCenter
        Layout.bottomMargin: 18
        Layout.preferredWidth: 360
        Layout.preferredHeight: 214
        radius: 10
        color: Theme.dark ? "#101118" : "#1B1D24"
        Rectangle {
            anchors.fill: parent
            anchors.margins: 8
            radius: 4
            clip: true
            color: "#0E1846"
            Image {
                anchors.fill: parent
                source: page.previewSource
                sourceSize.width: 720
                sourceSize.height: 400
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
            }
            Column {
                anchors.horizontalCenter: parent.horizontalCenter
                y: parent.height * 0.11
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: Qt.formatTime(page.now, Qt.locale().timeFormat(Locale.ShortFormat)
                                                  .replace(/\s*[aA][pP]\s*/, "").replace(/\s*t+\s*/, ""))
                    color: "#FFFFFF"
                    font.pixelSize: 30
                    font.weight: Font.DemiBold
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: Qt.locale().toString(page.now, backend.text("lock_date_format"))
                    color: "#FFFFFF"
                    font.pixelSize: 9
                }
            }
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-desktop-wallpaper-symbolic"
        title: backend.text("personalize_lock")
        description: backend.text("choose_photo")
        wrapControl: true

        WallpaperTiles {
            Layout.fillWidth: true
            wallpapers: page.wallpapers
            currentPath: page.lockPath
            // The desktop's own picture too, so it can be used here as well.
            extraPaths: [page.personal.lockWallpaper || "", page.personal.wallpaper || ""]
            onChosen: path => backend.setLockWallpaper(path)
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "folder-pictures-symbolic"
        title: backend.text("choose_photo")
        VButton {
            text: backend.text("browse_photos")
            onClicked: backend.browseLockWallpaper()
        }
    }

    SectionLabel {
        text: backend.text("lock_section")
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "system-lock-screen-symbolic"
        title: backend.text("auto_lock")
        ToggleSwitch {
            checked: page.p.autoLock !== false
            enabledState: page.p.loaded === true
            accessibleName: backend.text("auto_lock")
            onToggled: on => backend.setPref("autoLock", on)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-system-time-symbolic"
        title: backend.text("lock_after")
        VComboBox {
            Layout.preferredWidth: 200
            accessibleName: backend.text("lock_after")
            enabledState: page.p.loaded === true
            options: backend.lockOptions
            currentValue: page.p.autoLock === false ? 0 : page.p.lockAfter
            onActivated: value => backend.setPref("lockAfter", value)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "dialog-password-symbolic"
        title: backend.text("lock_on_resume")
        ToggleSwitch {
            checked: page.p.lockOnResume !== false
            enabledState: page.p.loaded === true
            accessibleName: backend.text("lock_on_resume")
            onToggled: on => backend.setPref("lockOnResume", on)
        }
    }
}
