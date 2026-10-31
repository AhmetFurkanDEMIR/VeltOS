/*
    VeltOS installer: the first page itself (loaded by welcomeq.qml), in
    the layout of Windows 11's setup: the VeltOS logo, a welcome, and the
    language for the installation and the new PC. While Calamares checks
    the PC (a few seconds; Next is off meanwhile) a progress ring says so.
    Requirements the PC does not meet appear as a Windows 11 InfoBar under
    the list: red when the installation cannot continue, yellow for a
    recommendation.

    Calamares provides `config` (welcome module: languagesModel,
    localeIndex, requirementsModel, unsatisfiedRequirements) and `ViewManager`.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.core 1.0
import io.calamares.ui 1.0

import QtQml
import QtQuick
import QtQuick.Layouts

import "VeltTheme.js" as Theme
import "LanguageOrder.js" as LanguageOrder

VeltPage {
    id: page

    picture: "ill-language.svg"
    showLogo: true
    // Choosing a language changes the texts on this page at once.
    languageTick: config.localeIndex
    title: t("Welcome to VeltOS", "VeltOS'a hoş geldiniz")
    subtitle: t("Choose your language. VeltOS uses it for the installation and on your PC; you can change it later in Settings.",
                "Dilinizi seçin. VeltOS bu dili kurulumda ve bilgisayarınızda kullanır; daha sonra Ayarlar'dan değiştirebilirsiniz.")

    // Calamares' languages with Türkçe and English first (item 38,
    // LanguageOrder.js); the list shows these rows, Calamares keeps its own
    // row numbers (`index`).
    property var languageRows: []

    function readLanguages() {
        const rows = [];
        for (let i = 0; i < languageSource.count; ++i) {
            const row = languageSource.objectAt(i);
            if (row)
                rows.push({ index: row.row, label: row.label, englishLabel: row.englishLabel });
        }
        languageRows = LanguageOrder.order(rows);
    }

    function showLanguage() {
        languages.show(LanguageOrder.position(languageRows, config.localeIndex));
    }

    Instantiator {
        id: languageSource
        model: config.languagesModel
        delegate: QtObject {
            readonly property int row: index
            readonly property string label: model.label
            readonly property string englishLabel: model.englishLabel
        }
        onObjectAdded: page.readLanguages()
        onObjectRemoved: page.readLanguages()
    }

    onActivated: {
        showLanguage();
        languages.focusList();
    }

    Component.onCompleted: {
        readLanguages();
        showLanguage();
    }

    VeltList {
        id: languages
        Layout.fillWidth: true
        Layout.fillHeight: true
        model: page.languageRows
        roleName: "label"
        detailRole: "englishLabel"
        currentIndex: LanguageOrder.position(page.languageRows, config.localeIndex)
        onChosen: (position) => {
            config.localeIndex = page.languageRows[position].index;
            languages.show(position);
        }
    }

    // Calamares checks the PC before Next turns on; say so, as Windows does.
    // (config.isNextEnabled is for pages that decide it themselves and stays
    // false here; ViewManager.nextEnabled is the Next button's state.)
    RowLayout {
        id: checking
        objectName: "checking"
        visible: !ViewManager.nextEnabled && requirements.count === 0
        spacing: 10
        VeltSpinner {
            Layout.preferredWidth: 18
            Layout.preferredHeight: 18
            running: checking.visible
        }
        Text {
            Layout.fillWidth: true
            text: page.t("Checking this PC…", "Bu bilgisayar denetleniyor…")
            color: Theme.c.subtext
            font.family: "Inter"
            font.pixelSize: 13
        }
    }

    VeltInfoBar {
        id: requirements
        visible: count > 0
        model: config.unsatisfiedRequirements
        role: "negatedText"
        severity: config.requirementsModel.satisfiedMandatory ? "warning" : "error"
        title: config.requirementsModel.satisfiedMandatory
               ? page.t("VeltOS will work, but this PC misses a recommendation",
                        "VeltOS çalışır, ancak bu bilgisayar bir öneriyi karşılamıyor")
               : page.t("VeltOS can't be installed on this PC",
                        "VeltOS bu bilgisayara kurulamaz")
    }
}
