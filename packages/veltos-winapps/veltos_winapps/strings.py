"""User-facing texts of the Windows app runner (English and Turkish)."""

import locale
import os

TEXTS = {
    "en": {
        "window_title": "Windows program",
        "unknown_publisher": "Unknown",
        "publisher": "Publisher: {publisher}",
        "version": "Version: {version}",
        "kind_installer": "Windows installer",
        "kind_program": "Windows program",
        "kind_batch": "Windows batch file",
        "trust_note": "Windows programs can read and change your personal files. "
                      "Only open programs from sources you trust.",
        "not_windows": "This file is not a Windows program VeltOS can open.",
        "preparing": "Setting up Windows compatibility…",
        "preparing_body": "This takes up to a minute the first time.",
        "installing": "Installing {name}",
        "installing_body": "Follow the steps in the installer window. The program will be added to Start.",
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
        "open": "Open",
        "open_app": "Open {name}",
        "cancel": "Cancel",
        "close": "Close",
        "done_button": "Done",
        "installer_done": "The installer is finished",
        "details": "Show details",
        "no_space": "Not enough free space",
        "no_space_body": "Windows programs need about {needed} MB of free space. "
                         "Free up some space and try again.",
        "no_space_live": "You are running VeltOS from the installation medium, where space for "
                         "Windows programs is limited by the computer's memory (about {needed} MB "
                         "are needed). Install VeltOS to use Windows programs.",
        "choose_runner": "How do you want to open {name}?",
        "choose_runner_body": "Other programs that run Windows software are installed on this PC.",
        "runner_wine": "VeltOS",
        "runner_wine_desc": "Opens at once in VeltOS' Windows environment (recommended)",
        "runner_bottles_desc": "Keeps Windows programs in separate bottles",
        "runner_lutris_desc": "Game library with its own runners",
        "runner_playonlinux_desc": "Installs Windows programs with scripts",
    },
    "tr": {
        "window_title": "Windows programı",
        "unknown_publisher": "Bilinmiyor",
        "publisher": "Yayımcı: {publisher}",
        "version": "Sürüm: {version}",
        "kind_installer": "Windows kurulum programı",
        "kind_program": "Windows programı",
        "kind_batch": "Windows toplu iş dosyası",
        "trust_note": "Windows programları kişisel dosyalarınızı okuyup değiştirebilir. "
                      "Yalnızca güvendiğiniz kaynaklardan gelen programları açın.",
        "not_windows": "Bu dosya VeltOS'un açabileceği bir Windows programı değil.",
        "preparing": "Windows uyumluluğu hazırlanıyor…",
        "preparing_body": "İlk seferde bu bir dakika kadar sürebilir.",
        "installing": "{name} kuruluyor",
        "installing_body": "Kurulum penceresindeki adımları izleyin. Program Başlat menüsüne eklenecek.",
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
        "open": "Aç",
        "open_app": "{name} uygulamasını aç",
        "cancel": "İptal",
        "close": "Kapat",
        "done_button": "Bitti",
        "installer_done": "Kurulum programı bitti",
        "details": "Ayrıntıları göster",
        "no_space": "Yeterli boş alan yok",
        "no_space_body": "Windows programları için yaklaşık {needed} MB boş alan gerekiyor. "
                         "Biraz yer açıp yeniden deneyin.",
        "no_space_live": "VeltOS'u kurulum ortamından çalıştırıyorsunuz; burada Windows programları "
                         "için alan bilgisayarın belleğiyle sınırlıdır (yaklaşık {needed} MB "
                         "gerekiyor). Windows programlarını kullanmak için VeltOS'u kurun.",
        "choose_runner": "{name} nasıl açılsın?",
        "choose_runner_body": "Bu bilgisayarda Windows yazılımı çalıştıran başka programlar da kurulu.",
        "runner_wine": "VeltOS",
        "runner_wine_desc": "VeltOS'un Windows ortamında hemen açılır (önerilen)",
        "runner_bottles_desc": "Windows programlarını ayrı şişelerde tutar",
        "runner_lutris_desc": "Kendi çalıştırıcılarıyla oyun kitaplığı",
        "runner_playonlinux_desc": "Windows programlarını betiklerle kurar",
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
