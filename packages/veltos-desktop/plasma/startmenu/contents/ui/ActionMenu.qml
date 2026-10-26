/*
    Context menu for Start menu items. Shows the item's own actions from
    Plasma's models (e.g. "Add to Desktop", "Edit Application…") plus
    "Pin to Start"/"Unpin from Start".

    Adapted from KDE Kickoff's ActionMenu.qml
    (SPDX-FileCopyrightText: 2013 Aurélien Gâteau, 2021 Noah Davis;
    SPDX-License-Identifier: GPL-2.0-or-later). Changes: no singleton,
    VeltOS pin actions, simplified sub-menu handling.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import org.kde.plasma.extras as PlasmaExtras

Item {
    id: root

    property var actionList: null
    property var model: null
    property int index: -1

    signal pinRequested(string favoriteId)
    signal unpinRequested(string favoriteId)
    signal shortcutRequested(string source)
    signal closeRequested()

    readonly property PlasmaExtras.Menu menu: PlasmaExtras.Menu {
        visualParent: null
        placement: PlasmaExtras.Menu.BottomPosedLeftAlignedPopup
    }

    visible: false

    Instantiator {
        active: root.actionList !== null
        model: root.actionList
        delegate: PlasmaExtras.MenuItem {
            required property var modelData

            text: modelData.text ?? ""
            enabled: modelData.type !== "title" && (modelData.enabled ?? true)
            separator: modelData.type === "separator"
            section: modelData.type === "title"
            icon: modelData.icon ?? null
            checkable: modelData.checkable ?? false
            checked: modelData.checked ?? false

            onClicked: {
                const actionId = modelData.actionId ?? "";
                if (actionId === "_veltos_pin") {
                    root.pinRequested(modelData.actionArgument);
                } else if (actionId === "_veltos_unpin") {
                    root.unpinRequested(modelData.actionArgument);
                } else if (actionId === "_veltos_create_shortcut") {
                    root.shortcutRequested(String(modelData.actionArgument ?? ""));
                    root.closeRequested();
                } else if (root.model && root.model.trigger(root.index, actionId, modelData.actionArgument)) {
                    root.closeRequested();
                }
            }
        }
        onObjectAdded: (index, object) => root.menu.addMenuItem(object)
        onObjectRemoved: (index, object) => root.menu.removeMenuItem(object)
    }
}
