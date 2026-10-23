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
    # OK / Cancel, as the product owner asked (2026-10-22), instead of
    # Windows' own Yes / No.
    "yes": ("OK", "Tamam"),
    "no": ("Cancel", "İptal"),
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


def polkit_locale(environ=None, lang=None):
    """The locale the agent gives polkit when it registers: polkit writes
    the messages it passes on ("Authentication is required to ...") in it,
    from the policy files' translations. The bare language ("tr") found
    only some of them; the session's full locale ("tr_TR.UTF-8") lets
    polkit also use the programs' message catalogs (gettext)."""
    environ = os.environ if environ is None else environ
    for variable in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = environ.get(variable, "")
        if value and value not in ("C", "POSIX", "C.UTF-8", "C.utf8"):
            if lang is None or value.lower().startswith(lang):
                return value
    lang = lang or language(environ)
    return "tr_TR.UTF-8" if lang == "tr" else "en_US.UTF-8"


def text(lang, key):
    pair = TEXTS[key]
    return pair[1] if lang == "tr" else pair[0]
