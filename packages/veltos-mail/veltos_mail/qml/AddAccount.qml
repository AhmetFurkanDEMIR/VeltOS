// "Add your account", as Windows 11's new Outlook asks for it: the address
// first; then the password (an app password where the provider wants one,
// with the link to make it), the person's name and, if needed, the
// servers (Advanced settings); signing in; "You're all set!". Outlook.com
// addresses are told plainly that they need Microsoft's own sign-in.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: page

    property string step: "email"          // email, password, oauth, done
    property var info: ({})
    property string error: ""
    property bool passwordWrong: false
    property bool checking: false
    property bool advanced: false
    signal finished()

    function reset() {
        step = "email";
        error = "";
        checking = false;
        advanced = false;
        emailField.text = "";
        passwordField.text = "";
        emailField.forceActiveFocus();
    }
    function next() {
        error = "";
        info = backend.providerInfo(emailField.text);
        if (!info.valid) {
            error = backend.text("bad_address");
            return;
        }
        if (info.auth === "oauth_only" && !info.oauthAvailable) {
            step = "oauth";
            return;
        }
        step = "password";
        nameField.text = nameField.text || backend.userName;
        passwordField.forceActiveFocus();
    }
    function submit() {
        error = "";
        passwordWrong = false;
        backend.addAccount({
            email: emailField.text, name: nameField.text, password: passwordField.text,
            imapHost: advanced ? imapHost.text : "", imapPort: imapPort.text, imapSecurity: imapSecurity.currentValue,
            smtpHost: advanced ? smtpHost.text : "", smtpPort: smtpPort.text, smtpSecurity: smtpSecurity.currentValue,
            username: advanced ? userField.text : ""
        });
    }

    color: Theme.canvas

    // A soft brand glow behind the card.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: Theme.dark ? "#13263A" : "#DCEBFA" }
            GradientStop { position: 0.55; color: Theme.canvas }
        }
    }

    Connections {
        target: backend
        function onAddAccountState(state, detail) {
            page.checking = state === "checking";
            if (state === "error") {
                page.error = backend.text(detail);
                page.passwordWrong = detail === "wrong_password" || detail === "app_password_error";
                if (detail === "oauth_needed")
                    page.step = "oauth";
                else if (detail === "no_server")
                    page.advanced = true;
            } else if (state === "done") {
                page.step = "done";
            }
        }
    }

    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(parent.width - 48, Math.round(460 * Theme.textScale))
        height: Math.min(parent.height - 48, content.implicitHeight + 64)
        radius: 8
        color: Theme.card
        border.width: Theme.dark ? 1 : 0
        border.color: Theme.cardBorder
        // A soft shadow: a few faint layers instead of one grey band.
        Repeater {
            model: 8
            delegate: Rectangle {
                required property int index
                z: -1
                anchors.fill: parent
                anchors.margins: -index
                anchors.topMargin: -index + 2
                anchors.bottomMargin: -index - 3
                radius: 8 + index
                color: "transparent"
                border.width: 1
                border.color: Qt.rgba(0, 0, 0, (Theme.dark ? 0.2 : 0.05) * (1 - index / 8))
            }
        }

        Flickable {
            anchors.fill: parent
            anchors.margins: 32
            contentHeight: content.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            ColumnLayout {
                id: content
                width: parent.width
                spacing: 14

                Kirigami.Icon {
                    Layout.preferredWidth: 56
                    Layout.preferredHeight: 56
                    source: "veltos-mail"
                    visible: page.step !== "done"
                }

                // --- 1. the address -------------------------------------------------------
                Text {
                    visible: page.step === "email"
                    Layout.fillWidth: true
                    text: backend.hasAccounts ? backend.text("add_title") : backend.text("welcome_title")
                    color: Theme.text
                    font.pixelSize: Theme.titleFont
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                }
                Text {
                    visible: page.step === "email" && !backend.hasAccounts
                    Layout.fillWidth: true
                    text: backend.text("add_title")
                    color: Theme.text
                    font.pixelSize: Math.round(16 * Theme.textScale)
                    font.weight: Font.DemiBold
                }
                Text {
                    visible: page.step === "email"
                    Layout.fillWidth: true
                    text: backend.text("add_sub")
                    color: Theme.subtext
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.Wrap
                }
                Field {
                    id: emailField
                    visible: page.step === "email"
                    Layout.fillWidth: true
                    Layout.topMargin: 6
                    placeholder: backend.text("email_placeholder")
                    error: page.error !== "" && page.step === "email"
                    input.inputMethodHints: Qt.ImhEmailCharactersOnly | Qt.ImhNoAutoUppercase
                    onAccepted: page.next()
                    Accessible.name: backend.text("email_label")
                }

                // --- 2. the password ------------------------------------------------------
                Text {
                    visible: page.step === "password"
                    Layout.fillWidth: true
                    text: page.info.title ? backend.textWith("sync_title", page.info.title) : backend.text("sync_title_plain")
                    color: Theme.text
                    font.pixelSize: Theme.titleFont
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                }
                RowLayout {
                    visible: page.step === "password"
                    spacing: 8
                    Glyph { Layout.preferredWidth: 18; Layout.preferredHeight: 18; kind: "person"; color: Theme.subtext }
                    Text { text: emailField.text; color: Theme.text; font.pixelSize: Theme.fontSize }
                    Text {
                        text: backend.text("back")
                        color: Theme.brandText
                        font.pixelSize: Theme.smallFont + 1
                        HoverHandler { cursorShape: Qt.PointingHandCursor }
                        TapHandler { onTapped: { page.step = "email"; page.error = ""; } }
                    }
                }
                Text {
                    visible: page.step === "password" && page.info.auth === "app_password"
                    Layout.fillWidth: true
                    text: backend.textWith("app_password_note", page.info.title || "")
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont + 1
                    wrapMode: Text.Wrap
                }
                Text {
                    visible: page.step === "password" && page.info.auth === "app_password" && !!page.info.help
                    text: backend.text("create_app_password")
                    color: Theme.brandText
                    font.pixelSize: Theme.smallFont + 1
                    font.underline: helpHover.hovered
                    HoverHandler { id: helpHover; cursorShape: Qt.PointingHandCursor }
                    TapHandler { onTapped: backend.openUrl(page.info.help) }
                }
                Text {
                    visible: page.step === "password"
                    text: backend.text("your_name")
                    color: Theme.text
                    font.pixelSize: Theme.smallFont + 1
                }
                Field {
                    id: nameField
                    visible: page.step === "password"
                    Layout.fillWidth: true
                }
                Text {
                    visible: page.step === "password"
                    text: page.info.auth === "app_password" ? backend.text("app_password") : backend.text("password")
                    color: Theme.text
                    font.pixelSize: Theme.smallFont + 1
                }
                Field {
                    id: passwordField
                    visible: page.step === "password"
                    Layout.fillWidth: true
                    echoMode: TextInput.Password
                    error: page.passwordWrong && page.step === "password"
                    onAccepted: page.submit()
                }

                // Advanced settings
                RowLayout {
                    visible: page.step === "password"
                    spacing: 6
                    Glyph {
                        Layout.preferredWidth: 12; Layout.preferredHeight: 12
                        kind: page.advanced ? "chevron-down" : "chevron-right"; color: Theme.brandText
                    }
                    Text {
                        text: backend.text("advanced")
                        color: Theme.brandText
                        font.pixelSize: Theme.smallFont + 1
                    }
                    HoverHandler { cursorShape: Qt.PointingHandCursor }
                    TapHandler { onTapped: page.advanced = !page.advanced }
                }
                GridLayout {
                    visible: page.step === "password" && page.advanced
                    Layout.fillWidth: true
                    columns: 3
                    columnSpacing: 8
                    rowSpacing: 6
                    Text { Layout.columnSpan: 3; text: backend.text("incoming"); color: Theme.text
                           font.pixelSize: Theme.smallFont + 1; font.weight: Font.DemiBold }
                    Field { id: imapHost; Layout.fillWidth: true; placeholder: backend.text("server") }
                    Field { id: imapPort; Layout.preferredWidth: 70; text: "993"; placeholder: backend.text("port") }
                    ComboBox {
                        id: imapSecurity
                        Layout.preferredWidth: 120
                        textRole: "text"; valueRole: "value"
                        model: [{ text: backend.text("security_ssl"), value: "ssl" },
                                { text: backend.text("security_starttls"), value: "starttls" }]
                    }
                    Text { Layout.columnSpan: 3; text: backend.text("outgoing_mail"); color: Theme.text
                           font.pixelSize: Theme.smallFont + 1; font.weight: Font.DemiBold }
                    Field { id: smtpHost; Layout.fillWidth: true; placeholder: backend.text("server") }
                    Field { id: smtpPort; Layout.preferredWidth: 70; text: "465"; placeholder: backend.text("port") }
                    ComboBox {
                        id: smtpSecurity
                        Layout.preferredWidth: 120
                        textRole: "text"; valueRole: "value"
                        model: [{ text: backend.text("security_ssl"), value: "ssl" },
                                { text: backend.text("security_starttls"), value: "starttls" }]
                        onActivated: smtpPort.text = currentValue === "ssl" ? "465" : "587"
                    }
                    Field { id: userField; Layout.columnSpan: 3; Layout.fillWidth: true; placeholder: backend.text("username") }
                }

                // --- Outlook.com and friends ----------------------------------------------
                Text {
                    visible: page.step === "oauth"
                    Layout.fillWidth: true
                    text: backend.text("oauth_needed")
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.Wrap
                }

                // --- done ----------------------------------------------------------------------
                Rectangle {
                    visible: page.step === "done"
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 64
                    Layout.preferredHeight: 64
                    radius: 32
                    color: Theme.brandSoft
                    Glyph { anchors.centerIn: parent; width: 32; height: 32; kind: "check"; color: Theme.brandText; lineWidth: 2 }
                }
                Text {
                    visible: page.step === "done"
                    Layout.alignment: Qt.AlignHCenter
                    text: backend.text("done_title")
                    color: Theme.text
                    font.pixelSize: Theme.titleFont
                    font.weight: Font.DemiBold
                }
                Text {
                    visible: page.step === "done"
                    Layout.alignment: Qt.AlignHCenter
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: backend.textWith("done_sub", emailField.text)
                    color: Theme.subtext
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.Wrap
                }

                // Error and progress
                Text {
                    visible: page.error !== "" && page.step !== "oauth"
                    Layout.fillWidth: true
                    text: page.error
                    color: Theme.danger
                    font.pixelSize: Theme.smallFont + 1
                    wrapMode: Text.Wrap
                }
                RowLayout {
                    visible: page.checking
                    spacing: 8
                    BusyIndicator { Layout.preferredWidth: 20; Layout.preferredHeight: 20; running: page.checking }
                    Text { text: backend.text("checking"); color: Theme.subtext; font.pixelSize: Theme.smallFont + 1 }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 10
                    spacing: 8
                    Text {
                        visible: page.step === "password"
                        Layout.fillWidth: true
                        text: backend.text("privacy_note")
                        color: Theme.tertiary
                        font.pixelSize: Theme.captionFont + 1
                        wrapMode: Text.Wrap
                    }
                    Item { Layout.fillWidth: true; visible: page.step !== "password" }
                    VButton {
                        visible: page.step === "oauth"
                        text: backend.text("open_web")
                        icon: "globe"
                        onClicked: backend.openUrl("https://outlook.live.com/mail/")
                    }
                    VButton {
                        visible: (page.step === "email" && backend.hasAccounts) || page.step === "oauth"
                        text: page.step === "oauth" ? backend.text("back") : backend.text("cancel")
                        onClicked: {
                            if (page.step === "oauth") { page.step = "email"; page.error = ""; }
                            else page.finished();
                        }
                    }
                    VButton {
                        visible: page.step === "email" || page.step === "password"
                        primary: true
                        active: !page.checking && (page.step === "email" ? emailField.text.trim() !== ""
                                                                          : passwordField.text !== "")
                        text: backend.text("continue")
                        onClicked: page.step === "email" ? page.next() : page.submit()
                    }
                    VButton {
                        visible: page.step === "done"
                        primary: true
                        text: backend.text("done")
                        onClicked: page.finished()
                    }
                }
            }
        }
    }
}
