"""User-facing texts of the Windows app runner (English and Turkish)."""

import locale
import os

TEXTS = {
    "en": {
        "window_title": "Windows program",
        "unknown_publisher": "Unknown publisher",
        "kind_installer": "Windows installer",
        "kind_program": "Windows program",
        "confirm_install": "Install {name} on VeltOS?",
        "confirm_install_body": "VeltOS will prepare a private Windows environment for this program, "
                                "start its installer and add the program to Start.",
        "confirm_run": "Open {name}?",
        "confirm_run_body": "This Windows program runs without installation.",
        "add_to_start": "Add to Start",
        "trust_note": "Windows programs can read and change your personal files. "
                      "Only open programs from sources you trust.",
        "not_windows": "This file is not a Windows program VeltOS can open.",
        "preparing": "Setting up Windows compatibility…",
        "preparing_body": "This takes up to a minute the first time.",
        "installing": "Installing {name}",
        "installing_body": "Follow the steps in the installer window.",
        "running": "Starting {name}…",
        "waiting": "Finishing installation…",
        "done": "{name} is installed",
        "done_body": "You can find it in Start.",
        "done_nothing": "The installer finished, but it did not add any program to Start. "
                        "If the program was installed, you can open it from its folder.",
        "failed": "{name} could not be started",
        "failed_install": "{name} could not be installed",
        "failed_body": "The program stopped with an error (code {code}). Some Windows programs "
                       "do not work on VeltOS yet.",
        "install": "Install",
        "open": "Open",
        "open_app": "Open {name}",
        "cancel": "Cancel",
        "close": "Close",
        "done_button": "Done",
        "installer_done": "The installer is finished",
        "details": "Show details",
    },
    "tr": {
        "window_title": "Windows programı",
        "unknown_publisher": "Bilinmeyen yayımcı",
        "kind_installer": "Windows kurulum programı",
        "kind_program": "Windows programı",
        "confirm_install": "{name} VeltOS'a kurulsun mu?",
        "confirm_install_body": "VeltOS bu program için özel bir Windows ortamı hazırlayacak, "
                                "kurulumu başlatacak ve programı Başlat menüsüne ekleyecek.",
        "confirm_run": "{name} açılsın mı?",
        "confirm_run_body": "Bu Windows programı kurulum gerektirmeden çalışır.",
        "add_to_start": "Başlat'a ekle",
        "trust_note": "Windows programları kişisel dosyalarınızı okuyup değiştirebilir. "
                      "Yalnızca güvendiğiniz kaynaklardan gelen programları açın.",
        "not_windows": "Bu dosya VeltOS'un açabileceği bir Windows programı değil.",
        "preparing": "Windows uyumluluğu hazırlanıyor…",
        "preparing_body": "İlk seferde bu bir dakika kadar sürebilir.",
        "installing": "{name} kuruluyor",
        "installing_body": "Kurulum penceresindeki adımları izleyin.",
        "running": "{name} başlatılıyor…",
        "waiting": "Kurulum tamamlanıyor…",
        "done": "{name} kuruldu",
        "done_body": "Programı Başlat menüsünde bulabilirsiniz.",
        "done_nothing": "Kurulum bitti ancak Başlat menüsüne bir program eklemedi. "
                        "Program kurulduysa klasöründen açabilirsiniz.",
        "failed": "{name} başlatılamadı",
        "failed_install": "{name} kurulamadı",
        "failed_body": "Program bir hatayla durdu (kod {code}). Bazı Windows programları "
                       "VeltOS'ta henüz çalışmıyor.",
        "install": "Kur",
        "open": "Aç",
        "open_app": "{name} uygulamasını aç",
        "cancel": "İptal",
        "close": "Kapat",
        "done_button": "Bitti",
        "installer_done": "Kurulum programı bitti",
        "details": "Ayrıntıları göster",
    },
}


def current_language():
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var, "")
        if value:
            return value.split(":")[0][:2]
    lang = (locale.getlocale()[0] or "en")[:2]
    return lang


class Texts:
    def __init__(self, language=None):
        self.table = TEXTS.get(language or current_language(), TEXTS["en"])

    def get(self, key, **values):
        text = self.table.get(key) or TEXTS["en"][key]
        return text.format(**values)
