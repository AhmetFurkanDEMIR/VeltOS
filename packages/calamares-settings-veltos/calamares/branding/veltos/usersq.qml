/*
    VeltOS installer: account page (Calamares module usersq), in the
    layout of Windows 11's "Who's going to use this device?": the user's
    name, the account name and the PC's name (both suggested from the name
    until the user changes them), a password typed twice, and automatic
    sign-in as a Windows 11 toggle switch. Problems show under the field
    they belong to.

    Calamares provides `config` (users module): fullName, loginName,
    hostname, their status messages, setUserPassword(Secondary),
    userPasswordValidity (0 valid, 1 weak, 2 invalid) and
    userPasswordMessage, doAutoLogin.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.core 1.0
import io.calamares.ui 1.0

import QtQuick
import QtQuick.Layouts

import "VeltTheme.js" as Theme

VeltPage {
    id: page

    picture: "ill-account.svg"
    title: t("Who's going to use this PC?", "Bu bilgisayarı kim kullanacak?")
    subtitle: t("Create the account you'll sign in with. You can add accounts for other people later in Settings.",
                "Oturum açacağınız hesabı oluşturun. Diğer kişiler için hesapları daha sonra Ayarlar'dan ekleyebilirsiniz.")

    // The password checks speak once both boxes have been typed in.
    readonly property bool passwordsTyped: password.text !== "" && confirm.text !== ""

    onActivated: fullName.focusField()

    VeltField {
        id: fullName
        label: page.t("Your name", "Adınız")
        placeholder: page.t("First and last name", "Adınız ve soyadınız")
        text: config.fullName
        enabledState: config.isEditable("fullName")
        onEdited: (text) => config.setFullName(text)
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 12
        uniformCellSizes: true
        VeltField {
            id: loginName
            label: page.t("Account name", "Hesap adı")
            placeholder: page.t("For example: alex", "Örneğin: ayse")
            // Suggested from the name until the user types here (Calamares keeps track).
            text: config.loginName
            enabledState: config.isEditable("loginName")
            message: { void page.t("", ""); return config.loginNameStatus; }
            onEdited: (text) => config.setLoginName(text)
        }
        VeltField {
            id: hostName
            label: page.t("PC name", "Bilgisayar adı")
            placeholder: page.t("For example: alex-pc", "Örneğin: ayse-pc")
            text: config.hostname
            message: { void page.t("", ""); return config.hostnameStatus; }
            onEdited: (text) => config.setHostName(text)
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 4
        spacing: 12
        uniformCellSizes: true
        VeltField {
            id: password
            password: true
            label: page.t("Password", "Parola")
            placeholder: page.t("Enter a password", "Bir parola girin")
            onEdited: (text) => config.setUserPassword(text)
        }
        VeltField {
            id: confirm
            password: true
            label: page.t("Confirm password", "Parolayı onaylayın")
            placeholder: page.t("Type it again", "Yeniden yazın")
            onEdited: (text) => config.setUserPasswordSecondary(text)
        }
    }
    Text {
        Layout.fillWidth: true
        Layout.topMargin: -4
        visible: text !== ""
        text: {
            void page.t("", "");
            if (!page.passwordsTyped || config.userPasswordValidity === 0)
                return "";
            return config.userPasswordMessage;
        }
        color: config.userPasswordValidity === 2 ? Theme.c.error : Theme.c.warning
        font.family: "Inter"
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }
    Text {
        Layout.fillWidth: true
        Layout.topMargin: -4
        text: page.t("Use this password to sign in, to unlock the PC and to approve changes to the system.",
                     "Bu parolayı oturum açmak, bilgisayarın kilidini açmak ve sistem değişikliklerini onaylamak için kullanırsınız.")
        color: Theme.c.subtext
        font.family: "Inter"
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }

    VeltToggle {
        Layout.fillWidth: true
        Layout.topMargin: 8
        label: page.t("Sign in automatically", "Otomatik olarak oturum aç")
        detail: page.t("VeltOS opens your desktop without asking for the password when the PC starts.",
                       "Bilgisayar açıldığında VeltOS parola sormadan masaüstünüzü açar.")
        checked: config.doAutoLogin
        onToggled: (checked) => config.setAutoLogin(checked)
    }

    Item {
        Layout.fillHeight: true
    }
}
