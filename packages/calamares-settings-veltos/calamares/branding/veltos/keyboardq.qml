/*
    VeltOS installer: keyboard page (Calamares module keyboardq), in the
    layout of Windows 11's "Is this the right keyboard layout or input
    method?": a search box, the layouts, the chosen layout's variants
    (Turkish Q, Turkish F, ...) and a box to try the keyboard. VeltOS does
    not offer the Kurdish variants that xkeyboard-config lists under the
    Turkish, Iraqi, Iranian and Syrian layouts (keys ku, ku_f, ku_alt,
    ku_ara; product owner, 2026-10-22).

    Calamares provides `config` (keyboard module): keyboardLayoutsModel and
    keyboardVariantsModel (roles label and key, a writable currentIndex;
    choosing a layout fills the variants and switches the keyboard at
    once).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.core 1.0
import io.calamares.ui 1.0

import QtQuick
import QtQuick.Layouts

VeltPage {
    id: page

    picture: "ill-keyboard.svg"
    title: t("Is this the right keyboard layout?", "Klavye düzeni doğru mu?")
    subtitle: t("Choose the layout printed on your keyboard, then try a few keys in the box below.",
                "Klavyenizin üzerindeki düzeni seçin, ardından aşağıdaki kutuda birkaç tuşu deneyin.")

    function fillLayouts() {
        const layouts = config.keyboardLayoutsModel;
        const wanted = search.text.trim().toLocaleLowerCase();
        layoutList.clear();
        for (let i = 0; i < layouts.rowCount(); i++) {
            const label = layouts.data(layouts.index(i, 0), Qt.DisplayRole);
            if (wanted !== "" && label.toLocaleLowerCase().indexOf(wanted) < 0)
                continue;
            layoutList.append({ label: label, source: i });
        }
        selectLayout();
    }

    // Mark the layout Calamares has chosen (it guesses one from the
    // language after the page has been shown).
    function selectLayout() {
        const wanted = config.keyboardLayoutsModel.currentIndex;
        let current = -1;
        for (let i = 0; i < layoutList.count; i++) {
            if (layoutList.get(i).source === wanted) {
                current = i;
                break;
            }
        }
        layoutView.currentIndex = current;
        layoutView.show(current);
    }

    function isOffered(variantKey) {
        const key = String(variantKey);
        return key !== "ku" && !key.startsWith("ku_");
    }

    // The chosen layout's variants (Calamares' model), the layout's default
    // first (as Windows lists it), without the Kurdish ones.
    function fillVariants() {
        const variants = config.keyboardVariantsModel;
        variantList.clear();
        for (let i = 0; i < variants.rowCount(); i++) {
            const index = variants.index(i, 0);
            const key = variants.data(index, Qt.UserRole);
            if (!isOffered(key))
                continue;
            const item = { label: variants.data(index, Qt.DisplayRole), source: i };
            if (key === "")
                variantList.insert(0, item);
            else
                variantList.append(item);
        }
        showVariant();
    }

    function showVariant() {
        const wanted = config.keyboardVariantsModel.currentIndex;
        let current = -1;
        for (let i = 0; i < variantList.count; i++) {
            if (variantList.get(i).source === wanted) {
                current = i;
                break;
            }
        }
        variantView.currentIndex = current;
        variantView.show(current);
    }

    onActivated: {
        // Layout names follow the language chosen on the first page.
        fillLayouts();
        fillVariants();
        layoutView.focusList();
    }

    Connections {
        target: config.keyboardLayoutsModel
        function onCurrentIndexChanged() { page.selectLayout(); }
    }
    // Calamares refills the variants when the layout changes and then picks one.
    Connections {
        target: config.keyboardVariantsModel
        function onCurrentIndexChanged() { Qt.callLater(page.showVariant); }
        function onModelReset() { Qt.callLater(page.fillVariants); }
    }

    ListModel {
        id: layoutList
    }

    ListModel {
        id: variantList
    }

    VeltField {
        id: search
        search: true
        placeholder: page.t("Search for a layout", "Düzen arayın")
        onEdited: page.fillLayouts()
        onAccepted: if (layoutList.count > 0) layoutView.chosen(0)
    }

    RowLayout {
        id: lists
        Layout.fillWidth: true
        Layout.fillHeight: true
        spacing: 12

        VeltList {
            id: layoutView
            Layout.preferredWidth: Math.round((lists.width - lists.spacing) * 0.5)
            Layout.fillHeight: true
            model: layoutList
            roleName: "label"
            empty: page.t("No layout found.", "Düzen bulunamadı.")
            onChosen: (index) => {
                config.keyboardLayoutsModel.currentIndex = layoutList.get(index).source;
                layoutView.currentIndex = index;
                layoutView.show(index);
            }
        }
        VeltList {
            id: variantView
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: variantList
            roleName: "label"
            onChosen: (index) => {
                config.keyboardVariantsModel.currentIndex = variantList.get(index).source;
                page.showVariant();
            }
        }
    }

    VeltField {
        placeholder: page.t("Type here to try your keyboard", "Klavyenizi denemek için buraya yazın")
    }
}
