"""User interface texts of VeltOS Settings (English and Turkish).

Texts of the individual settings live in catalog.py next to their items.
"""

import os

TEXTS = {
    "app_title": ("Settings", "Ayarlar"),
    "local_account": ("Local account", "Yerel hesap"),
    "find_setting": ("Find a setting", "Bir ayar bulun"),
    "control_panel": ("Control Panel", "Denetim Masası"),
    "control_panel_desc": ("Every setting, including advanced ones",
                           "Gelişmiş olanlar dahil tüm ayarlar"),
    "search_results": ("Search results", "Arama sonuçları"),
    "no_results": ("No settings found. Try other words, or look in the Control Panel.",
                   "Ayar bulunamadı. Başka sözcükler deneyin ya da Denetim Masası'na bakın."),
    # Home
    "home_welcome": ("Welcome, {name}", "Hoş geldiniz, {name}"),
    "rename": ("Rename", "Yeniden adlandır"),
    "recommended": ("Recommended settings", "Önerilen ayarlar"),
    "windows_programs_count": ("{count} Windows programs installed", "{count} Windows programı kurulu"),
    # Theme picker
    "theme": ("Theme", "Tema"),
    "theme_desc": ("Choose how VeltOS looks", "VeltOS'un görünümünü seçin"),
    "light": ("Light", "Açık"),
    "dark": ("Dark", "Koyu"),
    "theme_note": ("Open apps switch fully the next time they start.",
                   "Açık uygulamalar bir sonraki açılışta tamamen değişir."),
    # About
    "device_specs": ("Device specifications", "Cihaz özellikleri"),
    "device_name": ("Device name", "Cihaz adı"),
    "model": ("Model", "Model"),
    "processor": ("Processor", "İşlemci"),
    "threads": ("{count} threads", "{count} iş parçacığı"),
    "installed_ram": ("Installed RAM", "Yüklü RAM"),
    "graphics": ("Graphics", "Grafik"),
    "system_type": ("System type", "Sistem türü"),
    "os_specs": ("VeltOS specifications", "VeltOS özellikleri"),
    "edition": ("Edition", "Sürüm adı"),
    "version": ("Version", "Sürüm"),
    "kernel": ("Kernel", "Çekirdek"),
    "copy": ("Copy", "Kopyala"),
    "copied": ("Copied", "Kopyalandı"),
    "rename_pc": ("Rename this PC", "Bu bilgisayarı yeniden adlandır"),
    "rename_hint": ("Letters, numbers and spaces. You may be asked for your password.",
                    "Harf, rakam ve boşluk. Parolanız sorulabilir."),
    "ok": ("OK", "Tamam"),
    "cancel": ("Cancel", "İptal"),
    "unknown": ("Unknown", "Bilinmiyor"),
    # Storage
    "used_of": ("{used} used of {total}", "{total} alanın {used} kadarı kullanılıyor"),
    "free": ("{free} free", "{free} boş"),
    "system_drive": ("VeltOS", "VeltOS"),
    "live_drive": ("VeltOS (running from the install medium; files are kept in memory)",
                   "VeltOS (kurulum ortamından çalışıyor; dosyalar bellekte tutuluyor)"),
    "removable": ("Removable drive", "Çıkarılabilir sürücü"),
    "disk_management": ("Disk Management", "Disk Yönetimi"),
    "disk_management_desc": ("Partitions and formatting", "Bölümler ve biçimlendirme"),
    # Windows programs
    "windows_apps_intro": ("Programs you installed by opening a Windows .exe or .msi file. "
                           "They run in VeltOS's Windows environment (Wine), which is not a "
                           "security sandbox: install only programs you trust.",
                           "Bir Windows .exe veya .msi dosyası açarak kurduğunuz programlar. "
                           "VeltOS'un Windows ortamında (Wine) çalışırlar; bu ortam bir güvenlik "
                           "kum havuzu değildir: yalnızca güvendiğiniz programları kurun."),
    "no_windows_apps": ("No Windows programs yet. Double-click a .exe or .msi file to install one.",
                        "Henüz Windows programı yok. Kurmak için bir .exe veya .msi dosyasına çift tıklayın."),
    "open": ("Open", "Aç"),
    "uninstall_programs": ("Uninstall a program", "Program kaldır"),
    "uninstall_desc": ("Opens the Windows environment's list of installed programs",
                       "Windows ortamındaki kurulu programlar listesini açar"),
    "installed_on": ("Installed {date}", "Kurulum: {date}"),
}


def language(environ=None):
    environ = os.environ if environ is None else environ
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = environ.get(variable)
        if value:
            return "tr" if value.lower().startswith("tr") else "en"
    return "en"


def text(lang, key, **values):
    pair = TEXTS[key]
    result = pair[1] if lang == "tr" else pair[0]
    return result.format(**values) if values else result
