"""What VeltOS Settings shows: pages and the settings on them.

Every item does one of two things:
  * "page": show a page built into VeltOS Settings (About, Storage, ...);
  * "action": run something (open the Store, check for updates, ...).
KDE's own settings modules are never opened (the product owner's rule:
no old settings window anywhere); `systemsettings` and `kcmshell6` are
diverted to VeltOS Settings (bin/veltos-settings-redirect).

Icons are the monochrome Fluent symbolic icons ("-symbolic"), drawn in
the text colour like the line icons of Windows 11 Settings. Texts are
(English, Turkish) pairs; "keywords" are extra search words in both
languages.
"""

LANGUAGES = ("en", "tr")

# Pages built into the app (QML components, see Main.qml).
BUILTIN_PAGES = ("home", "about", "storage", "windows-apps", "display", "sound", "bluetooth",
                 "wifi", "background", "colours", "datetime", "notifications", "power",
                 "nightlight", "multitasking", "mouse", "touchpad", "keyboard", "lockscreen",
                 "defaultapps", "startup", "yourinfo", "signin", "otherusers", "region",
                 "accessibility", "searching", "themes", "taskbar", "location", "hotspot")
# Actions the backend knows (app.Backend.runAction).
ACTIONS = ("store", "updates", "uninstall-windows", "disk-management", "website")

# Navigation pane icons are monochrome line icons, as in Windows 11 Settings.
PAGES = [
    {"id": "home", "icon": "go-home-symbolic", "title": ("Home", "Giriş"), "builtin": True, "items": []},
    {"id": "system", "icon": "computer-symbolic", "title": ("System", "Sistem"), "items": [
        {"id": "display", "icon": "video-display-symbolic", "page": "display",
         "title": ("Display", "Ekran"),
         "desc": ("Monitors, resolution, scale, night light", "Monitörler, çözünürlük, ölçek, gece ışığı"),
         "keywords": "monitor screen resolution scale refresh hdr çözünürlük monitör"},
        {"id": "sound", "icon": "audio-volume-high-symbolic", "page": "sound",
         "title": ("Sound", "Ses"),
         "desc": ("Volume, output and input devices", "Ses düzeyi, çıkış ve giriş aygıtları"),
         "keywords": "audio speaker headphones microphone volume hoparlör kulaklık mikrofon"},
        {"id": "notifications", "icon": "preferences-system-notifications-symbolic", "page": "notifications",
         "title": ("Notifications", "Bildirimler"),
         "desc": ("Alerts from apps and the system, do not disturb",
                  "Uygulama ve sistem uyarıları, rahatsız etmeyin"),
         "keywords": "alerts do not disturb focus banner uyarı rahatsız"},
        {"id": "power", "icon": "battery-full-symbolic", "page": "power",
         "title": ("Power & battery", "Güç ve pil"),
         "desc": ("Sleep, screen off, power button", "Uyku, ekranı kapatma, güç düğmesi"),
         "keywords": "sleep battery energy suspend hibernate lid uyku enerji kapak"},
        {"id": "storage", "icon": "drive-harddisk-symbolic", "page": "storage",
         "title": ("Storage", "Depolama"),
         "desc": ("Space used on your drives", "Sürücülerinizde kullanılan alan"),
         "keywords": "disk drive space free ssd hdd alan sürücü"},
        {"id": "nightlight", "icon": "night-light-symbolic", "page": "nightlight",
         "title": ("Night light", "Gece ışığı"),
         "desc": ("Warmer colours in the evening", "Akşamları daha sıcak renkler"),
         "keywords": "blue light eye warm mavi ışık göz"},
        {"id": "multitasking", "icon": "view-dual-symbolic", "page": "multitasking",
         "title": ("Multitasking", "Çoklu görev"),
         "desc": ("Snap windows, desktops", "Pencereleri yaslama, masaüstleri"),
         "keywords": "snap desktops virtual workspaces yasla masaüstü sanal"},
        {"id": "about", "icon": "help-about-symbolic", "page": "about",
         "title": ("About", "Hakkında"),
         "desc": ("Device specifications, rename this PC, VeltOS version",
                  "Cihaz özellikleri, bu bilgisayarı yeniden adlandırma, VeltOS sürümü"),
         "keywords": "pc name computer hardware cpu ram gpu version bilgisayar adı donanım sürüm"},
    ]},
    {"id": "devices", "icon": "bluetooth-symbolic", "title": ("Bluetooth & devices", "Bluetooth ve cihazlar"), "items": [
        {"id": "bluetooth", "icon": "bluetooth-symbolic", "page": "bluetooth",
         "title": ("Bluetooth", "Bluetooth"),
         "desc": ("Pair headphones, mice, phones", "Kulaklık, fare ve telefon eşleştirme"),
         "keywords": "pair wireless eşleştir kablosuz"},
        {"id": "mouse", "icon": "input-mouse-symbolic", "page": "mouse",
         "title": ("Mouse", "Fare"),
         "desc": ("Buttons, pointer speed, scrolling", "Düğmeler, işaretçi hızı, kaydırma"),
         "keywords": "pointer cursor scroll left handed işaretçi solak"},
        {"id": "touchpad", "icon": "input-touchpad-symbolic", "page": "touchpad",
         "title": ("Touchpad", "Dokunmatik yüzey"),
         "desc": ("Taps, scrolling, cursor speed", "Dokunma, kaydırma, imleç hızı"),
         "keywords": "trackpad tap click scroll dokunma"},
        {"id": "keyboard", "icon": "input-keyboard-symbolic", "page": "keyboard",
         "title": ("Typing", "Yazma"),
         "desc": ("Keyboard layouts", "Klavye düzenleri"),
         "keywords": "layout keyboard q f türkçe klavye düzen"},
    ]},
    {"id": "network", "icon": "network-wireless-symbolic", "title": ("Network & internet", "Ağ ve internet"), "items": [
        {"id": "wifi", "icon": "network-wireless-symbolic", "page": "wifi",
         "title": ("Wi-Fi", "Wi-Fi"),
         "desc": ("Connect, manage known networks", "Bağlanma, bilinen ağları yönetme"),
         "keywords": "wireless wlan network password internet ethernet kablosuz ağ parola"},
        {"id": "hotspot", "icon": "network-wireless-hotspot-symbolic", "page": "hotspot",
         "title": ("Mobile hotspot", "Mobil etkin nokta"),
         "desc": ("Share your internet connection", "İnternet bağlantınızı paylaşın"),
         "keywords": "hotspot tethering share internet access point wifi paylaş etkin nokta erişim noktası"},
    ]},
    {"id": "personalization", "icon": "applications-graphics-symbolic", "title": ("Personalization", "Kişiselleştirme"), "theme_picker": True, "items": [
        {"id": "background", "icon": "preferences-desktop-wallpaper-symbolic", "page": "background",
         "title": ("Background", "Arka plan"),
         "desc": ("Desktop picture", "Masaüstü resmi"),
         "keywords": "wallpaper picture image duvar kağıdı resim"},
        {"id": "colors", "icon": "preferences-color-symbolic", "page": "colours",
         "title": ("Colours", "Renkler"),
         "desc": ("Light or dark mode, accent colour", "Açık veya koyu mod, vurgu rengi"),
         "keywords": "accent color colour dark light mode theme vurgu renk koyu açık tema"},
        {"id": "themes", "icon": "preferences-desktop-theme-symbolic", "page": "themes",
         "title": ("Themes", "Temalar"),
         "desc": ("Wallpaper, colour and mode together", "Duvar kağıdı, renk ve mod bir arada"),
         "keywords": "theme themes wallpaper colour look tema temalar duvar kağıdı görünüm"},
        {"id": "lockscreen", "icon": "system-lock-screen-symbolic", "page": "lockscreen",
         "title": ("Lock screen", "Kilit ekranı"),
         "desc": ("When to lock, password on wake", "Ne zaman kilitleneceği, uyanınca parola"),
         "keywords": "lock password screensaver kilit parola"},
        {"id": "taskbar", "icon": "view-app-grid-symbolic", "page": "taskbar",
         "title": ("Taskbar", "Görev çubuğu"),
         "desc": ("Taskbar items, system tray icons, taskbar behaviors",
                  "Görev çubuğu öğeleri, sistem tepsisi simgeleri, görev çubuğu davranışları"),
         "keywords": "taskbar search task view alignment center left hide badges combine tray "
                     "görev çubuğu arama hizalama ortala sol gizle birleştir tepsi"},
    ]},
    {"id": "apps", "icon": "view-app-grid-symbolic", "title": ("Apps", "Uygulamalar"), "items": [
        {"id": "windows-apps", "icon": "application-x-executable-symbolic", "page": "windows-apps",
         "title": ("Windows programs", "Windows programları"),
         "desc": ("Programs installed from .exe and .msi files", ".exe ve .msi dosyalarından kurulan programlar"),
         "keywords": "exe msi wine windows uninstall kaldır program"},
        {"id": "store", "icon": "view-app-grid-symbolic", "action": "store",
         "title": ("Get apps from the Store", "Mağazadan uygulama edinin"),
         "desc": ("Install and remove apps", "Uygulama kurma ve kaldırma"),
         "keywords": "install remove uninstall software discover kur kaldır yazılım mağaza"},
        {"id": "defaultapps", "icon": "preferences-desktop-apps-symbolic", "page": "defaultapps",
         "title": ("Default apps", "Varsayılan uygulamalar"),
         "desc": ("Web browser, email, music, photos, PDF", "Web tarayıcısı, e-posta, müzik, fotoğraf, PDF"),
         "keywords": "browser default open with file type tarayıcı varsayılan dosya türü"},
        {"id": "startup", "icon": "system-run-symbolic", "page": "startup",
         "title": ("Startup", "Başlangıç"),
         "desc": ("Apps that start when you sign in", "Oturum açınca başlayan uygulamalar"),
         "keywords": "autostart login boot başlangıç"},
    ]},
    {"id": "accounts", "icon": "avatar-default-symbolic", "title": ("Accounts", "Hesaplar"), "items": [
        {"id": "yourinfo", "icon": "user-info-symbolic", "page": "yourinfo",
         "title": ("Your info", "Bilgileriniz"),
         "desc": ("Name, profile photo", "Ad, profil fotoğrafı"),
         "keywords": "user account picture photo name kullanıcı hesap resim fotoğraf ad"},
        {"id": "signin", "icon": "dialog-password-symbolic", "page": "signin",
         "title": ("Sign-in options", "Oturum açma seçenekleri"),
         "desc": ("Password, lock on wake", "Parola, uyanınca kilitleme"),
         "keywords": "password change sign in parola değiştir oturum"},
        {"id": "otherusers", "icon": "system-users-symbolic", "page": "otherusers",
         "title": ("Other users", "Diğer kullanıcılar"),
         "desc": ("Add or remove people who use this PC", "Bu bilgisayarı kullananları ekleyin veya kaldırın"),
         "keywords": "users family add user administrator kullanıcı ekle yönetici aile"},
    ]},
    {"id": "time", "icon": "preferences-system-time-symbolic", "title": ("Time & language", "Saat ve dil"), "items": [
        {"id": "datetime", "icon": "preferences-system-time-symbolic", "page": "datetime",
         "title": ("Date & time", "Tarih ve saat"),
         "desc": ("Time zone, set the time automatically", "Saat dilimi, saati otomatik ayarlama"),
         "keywords": "clock timezone ntp saat dilimi"},
        {"id": "region", "icon": "preferences-desktop-locale-symbolic", "page": "region",
         "title": ("Language & region", "Dil ve bölge"),
         "desc": ("Display language, regional format", "Görüntüleme dili, bölgesel biçim"),
         "keywords": "language locale format türkçe english dil biçim"},
        {"id": "typing", "icon": "input-keyboard-symbolic", "page": "keyboard",
         "title": ("Typing", "Yazma"),
         "desc": ("Keyboard layouts", "Klavye düzenleri"),
         "keywords": "layout keyboard klavye"},
    ]},
    {"id": "gaming", "icon": "applications-games-symbolic", "title": ("Gaming", "Oyun"), "items": [
        {"id": "graphics", "icon": "video-display-symbolic", "page": "about",
         "title": ("Graphics", "Grafik"),
         "desc": ("Your graphics card", "Ekran kartınız"),
         "keywords": "gpu graphics card nvidia amd intel ekran kartı"},
    ]},
    {"id": "accessibility", "icon": "preferences-desktop-accessibility-symbolic", "title": ("Accessibility", "Erişilebilirlik"), "items": [
        {"id": "textsize", "icon": "preferences-desktop-font-symbolic", "page": "accessibility",
         "title": ("Text size", "Metin boyutu"),
         "desc": ("Make text bigger", "Yazıları büyütme"),
         "keywords": "font size bigger zoom büyüt yazı"},
        {"id": "effects", "icon": "applications-graphics-symbolic", "page": "accessibility",
         "title": ("Visual effects", "Görsel efektler"),
         "desc": ("Animation effects", "Animasyon efektleri"),
         "keywords": "animation motion animasyon hareket"},
    ]},
    {"id": "privacy", "icon": "preferences-system-privacy-symbolic", "title": ("Privacy & security", "Gizlilik ve güvenlik"), "items": [
        {"id": "location", "icon": "preferences-system-privacy-symbolic", "page": "location",
         "title": ("Location", "Konum"),
         "desc": ("Allow VeltOS Maps to access your location", "VeltOS Haritalar'ın konumunuza erişmesine izin verin"),
         "keywords": "location maps gps geoclue konum harita yer"},
        {"id": "lock", "icon": "system-lock-screen-symbolic", "page": "lockscreen",
         "title": ("Screen lock", "Ekran kilidi"),
         "desc": ("Lock automatically, ask for the password", "Otomatik kilitleme, parola sorma"),
         "keywords": "lock password kilit"},
        {"id": "searching", "icon": "system-search-symbolic", "page": "searching",
         "title": ("Searching files", "Dosya arama"),
         "desc": ("Index your files for search", "Arama için dosyalarınızı dizinleme"),
         "keywords": "index search arama dizin"},
    ]},
    {"id": "update", "icon": "view-refresh-symbolic", "title": ("VeltOS Update", "VeltOS Güncelleme"), "items": [
        {"id": "updates", "icon": "software-update-available-symbolic", "action": "updates",
         "title": ("Check for updates", "Güncellemeleri denetle"),
         "desc": ("Security fixes and app updates", "Güvenlik düzeltmeleri ve uygulama güncellemeleri"),
         "keywords": "update upgrade patch security güncelleme yama güvenlik"},
        {"id": "website", "icon": "internet-web-browser-symbolic", "action": "website",
         "title": ("VeltOS website", "VeltOS web sitesi"),
         "desc": ("News and help about VeltOS: veltos.ahmetfurkandemir.com",
                  "VeltOS hakkında haberler ve yardım: veltos.ahmetfurkandemir.com"),
         "keywords": "website web site help news veltos.ahmetfurkandemir.com site yardım haber"},
    ]},
]

# KDE settings module -> VeltOS Settings page (used by the redirect of
# `systemsettings` and `kcmshell6`; "home" for anything else).
KCM_PAGES = {
    "kcm_users": "yourinfo", "kcm_networkmanagement": "wifi", "kcm_wifi": "wifi",
    "kcm_bluetooth": "bluetooth", "kcm_pulseaudio": "sound", "kcm_kscreen": "display",
    "kcm_wallpaper": "background", "kcm_colors": "colours", "kcm_lookandfeel": "themes",
    "kcm_clock": "datetime", "kcm_powerdevilprofilesconfig": "power",
    "kcm_powerdevilglobalconfig": "power", "kcm_notifications": "notifications",
    "kcm_screenlocker": "lockscreen", "kcm_nightlight": "nightlight",
    "kcm_componentchooser": "defaultapps", "kcm_filetypes": "defaultapps",
    "kcm_autostart": "startup", "kcm_regionandlang": "region", "kcm_keyboard": "keyboard",
    "kcm_mouse": "mouse", "kcm_touchpad": "touchpad", "kcm_kwin_virtualdesktops": "multitasking",
    "kcm_kwinscreenedges": "multitasking", "kcm_about-distro": "about", "kcm_access": "accessibility",
    "kcm_fonts": "accessibility", "kcm_baloofile": "searching", "kcm_storage": "storage",
    # KDE's look modules: Windows keeps all of it under Personalization.
    "kcm_style": "colours", "kcm_icons": "colours", "kcm_desktoptheme": "themes",
    "kcm_kwindecoration": "colours", "kcm_cursortheme": "mouse", "kcm_splashscreen": "colours",
    "kcm_sddm": "lockscreen", "kcm_kwin_effects": "accessibility", "kcm_animations": "accessibility",
    "kcm_kwinoptions": "multitasking", "kcm_kwintabbox": "multitasking", "kcm_activities": "multitasking",
    "kcm_keys": "keyboard", "kcm_kded": "startup", "kcm_smserver": "power",
    "kcm_powerdevilactivitiesconfig": "power", "kcm_disks": "storage", "kcm_plasma-disks": "storage",
    "kcm_updates": "update", "kcm_bluedevil": "bluetooth", "kcm_wacomtablet": "mouse",
    "kcm_gamecontroller": "mouse", "kcm_soundtheme": "sound", "kcm_device_automounter": "storage",
    "kcm_solid_actions": "defaultapps", "kcm_webshortcuts": "searching", "kcm_plasmasearch": "searching",
    "kcm_landingpage": "home", "kcm_workspace": "multitasking", "kcm_screenlocker_kde": "lockscreen",
    # KDE Info Center's modules (kinfocenter opens VeltOS Settings too).
    "kcm_energyinfo": "power", "kcm_about": "about", "kcm_memory": "about", "kcm_cpu": "about",
    "kcm_pci": "about", "kcm_usb": "about", "kcm_opengl": "about", "kcm_vulkan": "about",
    "kcm_wayland": "about", "kcm_xserver": "about", "kcm_egl": "about", "kcm_glx": "about",
    "kcm_firmware_security": "about", "kcm_interrupts": "about", "kcm_kwinsupportinfo": "about",
    "kcm_block_devices": "storage", "kcm_audio_information": "sound", "kcm_network": "wifi",
    "kcm_samba": "about", "kcm_nic": "wifi", "kcm_edid": "display",
}


def page_for_module(name):
    """The VeltOS page for a KDE settings module name or a VeltOS page id."""
    name = (name or "").strip()
    if name.endswith(".desktop"):
        name = name[:-len(".desktop")]
    if name in KCM_PAGES:
        return KCM_PAGES[name]
    if name.startswith("kcm_") and "kcm_" + name[4:] in KCM_PAGES:
        return KCM_PAGES["kcm_" + name[4:]]
    if name in BUILTIN_PAGES or any(p["id"] == name for p in PAGES):
        return name
    return "home"


def page(page_id):
    for entry in PAGES:
        if entry["id"] == page_id:
            return entry
    raise KeyError(page_id)


def _pick(pair, lang):
    return pair[LANGUAGES.index(lang)] if lang in LANGUAGES else pair[0]


def localized_item(item, lang, page_entry=None):
    result = {
        "id": item["id"],
        "icon": item["icon"],
        "title": _pick(item["title"], lang),
        "description": _pick(item["desc"], lang),
        "page": item.get("page", ""),
        "action": item.get("action", ""),
    }
    if page_entry is not None:
        result["pageTitle"] = _pick(page_entry["title"], lang)
        result["pageId"] = page_entry["id"]
    return result


def localized_pages(lang):
    return [{
        "id": p["id"],
        "icon": p["icon"],
        "title": _pick(p["title"], lang),
        "builtin": p.get("builtin", False),
        "themePicker": p.get("theme_picker", False),
        "items": [localized_item(item, lang) for item in p["items"]],
    } for p in PAGES]


def fold(text):
    """Case-, accent- and punctuation-insensitive form for search
    (Turkish-aware): "Wi-Fi" and "wifi", "HOPARLÖR" and "hoparlor" match."""
    table = str.maketrans("İIıÇçĞğÖöŞşÜü", "iiiccggoossuu")
    folded = text.translate(table).casefold()
    return "".join(c for c in folded if c.isalnum() or c.isspace())


def search(query, lang):
    words = fold(query).split()
    if not words:
        return []
    results = []
    for p in PAGES:
        for item in p["items"]:
            haystack = fold(" ".join([*item["title"], *item["desc"], item.get("keywords", ""),
                                      *p["title"]]))
            if all(word in haystack for word in words):
                results.append(localized_item(item, lang, p))
    return results
