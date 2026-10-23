/*
    VeltOS installer: time zone page (Calamares module localeq), in the
    layout of Windows 11's "Is this the right country or region?": one
    list of cities with their region, a search box above it, and what the
    choice sets (time zone, language, formats) underneath.

    Calamares provides `config` (locale module): zonesModel (every zone:
    roles name = Qt.DisplayRole, key = Qt.UserRole, region = Qt.UserRole+1),
    regionModel (name, key), currentLocation (region, zone),
    setCurrentLocation(region, zone), currentTimezoneName and the status
    sentences. The language follows the first page, the formats follow
    the time zone's country (Calamares' rules).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.core 1.0
import io.calamares.ui 1.0

import QtQuick
import QtQuick.Layouts

import "VeltTheme.js" as Theme

VeltPage {
    id: page

    picture: "ill-region.svg"
    title: t("Is this the right time zone?", "Saat dilimi doğru mu?")
    subtitle: t("Choose the city closest to you. VeltOS sets the clock and the format of dates and numbers from it.",
                "Size en yakın şehri seçin. VeltOS saati, tarih ve sayı biçimlerini buna göre ayarlar.")

    property var zones: []          // every zone: { label, detail, region, zone }

    // All zones of all regions, sorted by the city's name in the current language.
    function collectZones() {
        const regionNames = {};
        const regions = config.regionModel;
        for (let i = 0; i < regions.rowCount(); i++) {
            const index = regions.index(i, 0);
            regionNames[regions.data(index, Qt.UserRole)] = regions.data(index, Qt.DisplayRole);
        }
        const result = [];
        const all = config.zonesModel;
        for (let i = 0; i < all.rowCount(); i++) {
            const index = all.index(i, 0);
            const region = all.data(index, Qt.UserRole + 1);
            result.push({
                label: all.data(index, Qt.DisplayRole),
                detail: regionNames[region] || region,
                region: region,
                zone: all.data(index, Qt.UserRole)
            });
        }
        const language = Qt.locale().name;
        result.sort((a, b) => a.label.localeCompare(b.label, language));
        page.zones = result;
    }

    function fillList() {
        const wanted = search.text.trim().toLocaleLowerCase();
        zoneList.clear();
        for (const z of page.zones) {
            if (wanted !== "" && z.label.toLocaleLowerCase().indexOf(wanted) < 0
                    && z.detail.toLocaleLowerCase().indexOf(wanted) < 0)
                continue;
            zoneList.append(z);
        }
        selectCurrent();
    }

    // Mark the time zone Calamares has chosen (it settles the location only
    // after the page has been shown).
    function selectCurrent() {
        const location = config.currentLocation;
        let current = -1;
        for (let i = 0; location && i < zoneList.count; i++) {
            const z = zoneList.get(i);
            if (z.region === location.region && z.zone === location.zone) {
                current = i;
                break;
            }
        }
        cities.currentIndex = current;
        cities.show(current);
    }

    Connections {
        target: config
        function onCurrentLocationChanged() { page.selectCurrent(); }
    }

    onActivated: {
        // City names follow the language chosen on the first page.
        collectZones();
        fillList();
        cities.focusList();
    }

    ListModel {
        id: zoneList
    }

    VeltField {
        id: search
        search: true
        placeholder: page.t("Search for a city", "Şehir arayın")
        onEdited: page.fillList()
        onAccepted: if (zoneList.count > 0) cities.chosen(0)
    }

    VeltList {
        id: cities
        Layout.fillWidth: true
        Layout.fillHeight: true
        model: zoneList
        roleName: "label"
        detailRole: "detail"
        empty: page.t("No city found. Try the name of a bigger city in your time zone.",
                      "Şehir bulunamadı. Saat diliminizdeki daha büyük bir şehrin adını deneyin.")
        onChosen: (index) => {
            const z = zoneList.get(index);
            config.setCurrentLocation(z.region, z.zone);
            cities.currentIndex = index;
            cities.show(index);
        }
    }

    // What the choice sets, as Calamares words it.
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: status.implicitHeight + 20
        radius: 8
        color: Theme.c.card
        border.width: 1
        border.color: Theme.c.border

        Canvas {
            id: clock
            x: 14
            y: 12
            width: 18
            height: 18
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = Theme.accent;
                ctx.lineWidth = 1.5;
                ctx.lineCap = "round";
                ctx.beginPath();
                ctx.arc(9, 9, 7.5, 0, 2 * Math.PI);
                ctx.moveTo(9, 4.5);
                ctx.lineTo(9, 9);
                ctx.lineTo(12, 11);
                ctx.stroke();
            }
        }
        ColumnLayout {
            id: status
            anchors.left: clock.right
            anchors.leftMargin: 12
            anchors.right: parent.right
            anchors.rightMargin: 14
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            Text {
                Layout.fillWidth: true
                text: page.t("Time zone: ", "Saat dilimi: ") + config.currentTimezoneName
                color: Theme.c.text
                font.family: "Inter"
                font.pixelSize: 13
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Text {
                Layout.fillWidth: true
                text: { void page.t("", ""); return config.currentLanguageStatus; }
                color: Theme.c.subtext
                font.family: "Inter"
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
            Text {
                Layout.fillWidth: true
                text: { void page.t("", ""); return config.currentLCStatus; }
                color: Theme.c.subtext
                font.family: "Inter"
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
        }
    }
}
