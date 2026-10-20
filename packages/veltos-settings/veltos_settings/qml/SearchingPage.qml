// Privacy & security > Searching files: whether the contents of the
// user's files are indexed for search (KDE's file indexer, balooctl6).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshPrefs()

    SettingRow {
        Layout.fillWidth: true
        icon: "system-search-symbolic"
        title: backend.text("search_indexing")
        description: backend.text("search_indexing_desc")
        ToggleSwitch {
            checked: page.p.fileSearch === true
            enabledState: page.p.loaded === true
            accessibleName: backend.text("search_indexing")
            onToggled: on => backend.setFileSearch(on)
        }
    }
}
