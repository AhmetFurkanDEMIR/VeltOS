/*
    VeltOS installer: "If you forget your password" (Calamares module
    notesqml, instance "recovery", after the account page). Two optional
    things, as Windows 11 offers them: a password hint shown on the
    sign-in screen after a wrong password, and a password reset USB, a
    USB flash drive the installation writes a long random key to (product
    owner, 2026-11-01). Without a drive VeltOS says plainly that a
    forgotten password cannot be reset.

    The page has no Calamares config object of its own, and Calamares'
    global storage cannot be written from QML: the choices go to
    install-veltos' helper (open-website, the signed-in user, 127.0.0.1,
    POST /choices), which keeps them for the password-recovery job. The USB
    drives come from the same helper (GET /drives, veltos-auth's
    password-recovery); the drive VeltOS runs from and the disks of this
    installation (read from global storage) are left out.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.core 1.0
import io.calamares.ui 1.0

import QtQuick
import QtQuick.Layouts

import "VeltTheme.js" as Theme

VeltPage {
    id: page

    readonly property string helper: "http://127.0.0.1:47823/drives"
    property bool wanted: false
    property var drives: []
    property string chosen: ""
    property bool loading: false

    picture: "ill-reset.svg"
    title: t("If you forget your password", "Parolanızı unutursanız")
    subtitle: t("Add a hint that reminds you of your password, and make a password reset USB to set a new password on the sign-in screen. Both are optional.",
                "Parolanızı hatırlatacak bir ipucu ekleyin ve oturum açma ekranında yeni parola belirleyebilmek için bir parola sıfırlama USB'si oluşturun. İkisi de isteğe bağlıdır.")

    // The disks this installation uses (Calamares' partition step, before
    // this page): a reset key never goes there.
    function targetDisks() {
        const disks = [];
        const parts = Global.value("partitions") || [];
        for (let i = 0; i < parts.length; i++) {
            const device = String(parts[i].device || "");
            const disk = device.replace(/(\d+)p\d+$/, "$1").replace(/([a-z])\d+$/, "$1");
            if (disk && disks.indexOf(disk) < 0)
                disks.push(disk);
        }
        return disks;
    }

    function sizeText(bytes) {
        const gb = bytes / 1e9;
        return gb >= 1 ? (Math.round(gb * 10) / 10).toLocaleString(Qt.locale()) + " GB"
                       : Math.round(bytes / 1e6) + " MB";
    }

    function refresh() {
        loading = true;
        const request = new XMLHttpRequest();
        request.onreadystatechange = function () {
            if (request.readyState !== XMLHttpRequest.DONE)
                return;
            page.loading = false;
            let found = [];
            try {
                found = JSON.parse(request.responseText) || [];
            } catch (error) {
                found = [];
            }
            page.drives = found.map(d => ({
                path: d.path,
                label: (d.label || d.model || page.t("USB drive", "USB sürücü")) + " (" + page.sizeText(d.size) + ")",
                detail: d.path
            }));
            if (!page.drives.some(d => d.path === page.chosen))
                page.chosen = page.drives.length === 1 ? page.drives[0].path : "";
            page.store();
        };
        request.open("GET", helper + "?exclude=" + encodeURIComponent(targetDisks().join(",")));
        request.send();
    }

    // Calamares 3.3.14's QML can read its global storage but not write it
    // (Global.insert is "not a function"): the choices go to the helper,
    // which keeps them for the password-recovery job.
    function store() {
        const request = new XMLHttpRequest();
        request.open("POST", "http://127.0.0.1:47823/choices");
        request.setRequestHeader("Content-Type", "application/json");
        request.send(JSON.stringify({ hint: hint.text.trim(), device: wanted ? chosen : "",
                                      exclude: targetDisks().join(",") }));
    }

    onActivated: {
        hint.focusField();
        if (wanted)
            refresh();
    }

    VeltField {
        id: hint
        label: page.t("Password hint (optional)", "Parola ipucu (isteğe bağlı)")
        placeholder: page.t("Something that reminds you of your password", "Size parolanızı hatırlatacak bir şey")
        hint: page.t("Shown on the sign-in screen after a wrong password; anyone at the PC can read it, so don't write the password itself.",
                     "Yanlış parola girildiğinde oturum açma ekranında görünür; bilgisayarın başındaki herkes okuyabilir, parolanın kendisini yazmayın.")
        maximumLength: 100
        onEdited: (text) => page.store()
    }

    VeltToggle {
        Layout.fillWidth: true
        Layout.topMargin: 8
        label: page.t("Make a password reset USB", "Parola sıfırlama USB'si oluştur")
        detail: page.t("VeltOS writes a long key to a USB flash drive; nothing on it is erased. With the drive you can set a new password on the sign-in screen. Keep it safe: anyone who has it can do that.",
                       "VeltOS bir USB belleğe uzun bir anahtar yazar; bellekteki hiçbir şey silinmez. Bu bellekle oturum açma ekranında yeni bir parola belirleyebilirsiniz. Güvenli bir yerde saklayın: belleği elinde tutan herkes bunu yapabilir.")
        checked: page.wanted
        onToggled: (checked) => {
            page.wanted = checked;
            if (checked)
                page.refresh();
            page.store();
        }
    }

    RowLayout {
        Layout.fillWidth: true
        visible: page.wanted
        spacing: 12
        Text {
            Layout.fillWidth: true
            text: page.t("Insert a USB flash drive (not the one VeltOS runs from) and choose it:",
                         "Bir USB bellek takın (VeltOS'un çalıştığı bellek değil) ve seçin:")
            color: Theme.c.text
            font.family: "Inter"
            font.pixelSize: 13
            wrapMode: Text.WordWrap
        }
        VeltButton {
            label: page.loading ? page.t("Looking…", "Aranıyor…") : page.t("Refresh", "Yenile")
            active: !page.loading
            onActivated: page.refresh()
        }
    }
    VeltList {
        id: driveList
        Layout.fillWidth: true
        Layout.preferredHeight: 132
        visible: page.wanted
        model: page.drives
        roleName: "label"
        detailRole: "detail"
        currentIndex: page.drives.findIndex(d => d.path === page.chosen)
        empty: page.loading ? "" : page.t("No USB flash drive found. Insert one, then select Refresh.",
                                          "USB bellek bulunamadı. Bir bellek takıp Yenile'yi seçin.")
        onChosen: (index) => {
            page.chosen = page.drives[index].path;
            page.store();
        }
    }

    VeltInfoBar {
        Layout.fillWidth: true
        Layout.topMargin: 4
        visible: !page.wanted || page.chosen === ""
        severity: "warning"
        title: page.t("Without a password reset USB, a forgotten password can't be reset.",
                      "Parola sıfırlama USB'si olmadan unutulan bir parola sıfırlanamaz.")
        lines: [page.t("You can make one later in Settings > Accounts > Sign-in options.",
                       "Daha sonra Ayarlar > Hesaplar > Oturum açma seçenekleri'nden oluşturabilirsiniz.")]
    }

    Item {
        Layout.fillHeight: true
    }
}
