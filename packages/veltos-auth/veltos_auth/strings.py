"""Texts of the VeltOS authentication prompt (English and Turkish), in
the words of Windows 11's User Account Control window."""

import os

TEXTS = {
    "title": ("User Account Control", "Kullanıcı Hesabı Denetimi"),
    "question": ("Do you want to allow this app to make changes to your device?",
                 "Bu uygulamanın cihazınızda değişiklik yapmasına izin vermek istiyor musunuz?"),
    "enter_password": ("To continue, enter an administrator password.",
                       "Devam etmek için bir yönetici parolası girin."),
    "password": ("Password", "Parola"),
    "yes": ("Yes", "Evet"),
    "no": ("No", "Hayır"),
    "administrator": ("Administrator", "Yönetici"),
    "wrong_password": ("The password is incorrect. Try again.", "Parola yanlış. Yeniden deneyin."),
    "show_details": ("Show more details", "Daha fazla ayrıntı göster"),
    "hide_details": ("Hide details", "Ayrıntıları gizle"),
    "action": ("Action", "Eylem"),
    "program": ("Program", "Program"),
    "caps_lock": ("Caps Lock is on", "Caps Lock açık"),
    "checking": ("Checking…", "Denetleniyor…"),
}


def language(environ=None):
    environ = os.environ if environ is None else environ
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = environ.get(variable)
        if value:
            return "tr" if value.lower().startswith("tr") else "en"
    return "en"


def text(lang, key):
    pair = TEXTS[key]
    return pair[1] if lang == "tr" else pair[0]
