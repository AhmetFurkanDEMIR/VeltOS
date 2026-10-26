import QtQuick
import org.kde.plasma.extras as PlasmaExtras

Item {
    id: root

    property var actionList: null
    property var targetModel: null
    property int targetIndex: -1

    signal actionTriggered()
    signal shortcutRequested(string source)

    readonly property PlasmaExtras.Menu menu: PlasmaExtras.Menu {
        visualParent: null
        placement: PlasmaExtras.Menu.BottomPosedLeftAlignedPopup
    }

    visible: false

    function openFor(anchor, model, index, actions) {
        if (!actions || actions.length === 0)
            return;
        targetModel = model;
        targetIndex = index;
        actionList = Array.from(actions);
        menu.visualParent = anchor;
        menu.openRelative();
    }

    Instantiator {
        active: root.actionList !== null
        model: root.actionList || []
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
                if (actionId === "_veltos_create_shortcut") {
                    root.shortcutRequested(String(modelData.actionArgument ?? ""));
                    root.actionTriggered();
                } else if (root.targetModel
                        && root.targetModel.trigger(root.targetIndex, actionId, modelData.actionArgument))
                    root.actionTriggered();
            }
        }
        onObjectAdded: (index, object) => root.menu.addMenuItem(object)
        onObjectRemoved: (index, object) => root.menu.removeMenuItem(object)
    }
}
