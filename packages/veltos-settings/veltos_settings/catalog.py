"""What VeltOS Settings shows: pages and the settings on them.

Every item does one of three things:
  * "kcm": open one of KDE's settings modules in its own window (the
    complete, maintained implementation of that setting);
  * "page": show a page built into VeltOS Settings (About, Storage, ...);
  * "action": run something (open the Store, the Control Panel, ...).

Texts are (English, Turkish) pairs; "keywords" are extra search words in
both languages.
"""

LANGUAGES = ("en", "tr")

# Pages built into the app (QML components in qml/pages/).
BUILTIN_PAGES = ("home", "about", "storage", "windows-apps", "display", "sound", "bluetooth",
                 "wifi", "background", "colours", "datetime")
# Actions the backend knows (app.Backend.runAction).
ACTIONS = ("control-panel", "store", "updates", "uninstall-windows", "disk-management")

# Navigation pane icons are monochrome line icons, as in Windows 11
# Settings; the settings on the pages keep their coloured icons.
PAGES = [
    {"id": "home", "icon": "go-home", "title": ("Home", "Giriş"), "builtin": True, "items": []},
    {"id": "system", "icon": "computer", "title": ("System", "Sistem"), "items": [
        {"id": "display", "icon": "preferences-desktop-display", "page": "display",
         "title": ("Display", "Ekran"),
         "desc": ("Monitors, resolution, scale, brightness", "Monitörler, çözünürlük, ölçek, parlaklık"),
         "keywords": "monitor screen resolution scale refresh hdr çözünürlük monitör"},
        {"id": "nightlight", "icon": "redshift-status-on", "kcm": "kcm_nightlight",
         "title": ("Night light", "Gece ışığı"),
         "desc": ("Warmer colours in the evening", "Akşamları daha sıcak renkler"),
         "keywords": "blue light eye mavi ışık göz"},
        {"id": "sound", "icon": "preferences-desktop-sound", "page": "sound",
         "title": ("Sound", "Ses"),
         "desc": ("Volume, output and input devices", "Ses düzeyi, çıkış ve giriş aygıtları"),
         "keywords": "audio speaker headphones microphone volume hoparlör kulaklık mikrofon"},
        {"id": "notifications", "icon": "preferences-desktop-notification", "kcm": "kcm_notifications",
         "title": ("Notifications", "Bildirimler"),
         "desc": ("Alerts from apps and the system, do not disturb",
                  "Uygulama ve sistem uyarıları, rahatsız etmeyin"),
         "keywords": "alerts do not disturb focus uyarı"},
        {"id": "power", "icon": "preferences-system-power-management", "kcm": "kcm_powerdevilprofilesconfig",
         "title": ("Power & battery", "Güç ve pil"),
         "desc": ("Sleep, screen off, power button, battery", "Uyku, ekranı kapatma, güç düğmesi, pil"),
         "keywords": "sleep battery energy suspend hibernate uyku enerji"},
        {"id": "storage", "icon": "drive-harddisk", "page": "storage",
         "title": ("Storage", "Depolama"),
         "desc": ("Space used on your drives", "Sürücülerinizde kullanılan alan"),
         "keywords": "disk drive space free ssd hdd alan sürücü"},
        {"id": "multitasking", "icon": "preferences-system-windows", "kcm": "kcm_kwin_virtualdesktops",
         "title": ("Multitasking", "Çoklu görev"),
         "desc": ("Virtual desktops", "Sanal masaüstleri"),
         "keywords": "desktops workspaces snap masaüstü"},
        {"id": "windowbehaviour", "icon": "preferences-system-windows-actions", "kcm": "kcm_kwinoptions",
         "title": ("Window behaviour", "Pencere davranışı"),
         "desc": ("Focus, titlebar actions, moving windows", "Odak, başlık çubuğu eylemleri, pencere taşıma"),
         "keywords": "windows focus click pencere"},
        {"id": "about", "icon": "help-about", "page": "about",
         "title": ("About", "Hakkında"),
         "desc": ("Device specifications, rename this PC, VeltOS version",
                  "Cihaz özellikleri, bu bilgisayarı yeniden adlandırma, VeltOS sürümü"),
         "keywords": "pc name computer hardware cpu ram gpu version bilgisayar adı donanım sürüm"},
    ]},
    {"id": "devices", "icon": "bluetooth", "title": ("Bluetooth & devices", "Bluetooth ve cihazlar"), "items": [
        {"id": "bluetooth", "icon": "preferences-system-bluetooth", "page": "bluetooth",
         "title": ("Bluetooth", "Bluetooth"),
         "desc": ("Pair headphones, mice, phones", "Kulaklık, fare ve telefon eşleştirme"),
         "keywords": "pair wireless eşleştir kablosuz"},
        {"id": "mouse", "icon": "input-mouse", "kcm": "kcm_mouse",
         "title": ("Mouse", "Fare"),
         "desc": ("Pointer speed, buttons, scrolling", "İşaretçi hızı, düğmeler, kaydırma"),
         "keywords": "pointer cursor scroll işaretçi"},
        {"id": "touchpad", "icon": "input-touchpad", "kcm": "kcm_touchpad",
         "title": ("Touchpad", "Dokunmatik yüzey"),
         "desc": ("Taps, gestures, scrolling", "Dokunma, hareketler, kaydırma"),
         "keywords": "trackpad gestures tap hareket"},
        {"id": "keyboard", "icon": "input-keyboard", "kcm": "kcm_keyboard",
         "title": ("Keyboard", "Klavye"),
         "desc": ("Layouts, repeat, NumLock", "Düzenler, tekrar, NumLock"),
         "keywords": "layout typing q f türkçe klavye düzen"},
        {"id": "touchscreen", "icon": "input-touchscreen", "kcm": "kcm_touchscreen",
         "title": ("Touch screen", "Dokunmatik ekran"),
         "desc": ("Which screen your touch screen controls", "Dokunmatik ekranın hangi ekranı yönettiği"),
         "keywords": "touch dokunma"},
        {"id": "tablet", "icon": "input-tablet", "kcm": "kcm_tablet",
         "title": ("Pen & tablet", "Kalem ve tablet"),
         "desc": ("Drawing tablets and pens", "Çizim tabletleri ve kalemler"),
         "keywords": "wacom stylus drawing çizim"},
        {"id": "gamecontroller", "icon": "input-gaming", "kcm": "kcm_gamecontroller",
         "title": ("Game controllers", "Oyun kumandaları"),
         "desc": ("Test and set up gamepads and joysticks", "Gamepad ve joystick testi ve ayarı"),
         "keywords": "gamepad joystick xbox playstation controller kumanda"},
    ]},
    {"id": "network", "icon": "network-wireless", "title": ("Network & internet", "Ağ ve internet"), "items": [
        {"id": "wifi", "icon": "network-wireless", "page": "wifi",
         "title": ("Wi-Fi", "Wi-Fi"),
         "desc": ("Connect, manage known networks", "Bağlanma, bilinen ağları yönetme"),
         "keywords": "wireless wlan network password internet kablosuz ağ parola"},
        {"id": "advancednetwork", "icon": "network-wired", "kcm": "kcm_networkmanagement",
         "title": ("Ethernet, VPN & advanced", "Ethernet, VPN ve gelişmiş"),
         "desc": ("Cable connections, VPN, hotspot, IP addresses",
                  "Kablolu bağlantılar, VPN, erişim noktası, IP adresleri"),
         "keywords": "lan cable ethernet hotspot vpn ip dns kablo internet"},
        {"id": "proxy", "icon": "preferences-system-network-proxy", "kcm": "kcm_proxy",
         "title": ("Proxy", "Ara sunucu"),
         "desc": ("Proxy server settings", "Ara sunucu ayarları"),
         "keywords": "proxy vekil"},
        {"id": "firewall", "icon": "security-high", "kcm": "kcm_firewall",
         "title": ("Firewall", "Güvenlik duvarı"),
         "desc": ("Allow or block network connections", "Ağ bağlantılarına izin verme veya engelleme"),
         "keywords": "firewall ufw security güvenlik"},
    ]},
    {"id": "personalization", "icon": "brush-symbolic", "title": ("Personalization", "Kişiselleştirme"), "theme_picker": True, "items": [
        {"id": "background", "icon": "preferences-desktop-wallpaper", "page": "background",
         "title": ("Background", "Arka plan"),
         "desc": ("Desktop picture", "Masaüstü resmi"),
         "keywords": "wallpaper picture image duvar kağıdı resim"},
        {"id": "colors", "icon": "preferences-desktop-color", "page": "colours",
         "title": ("Colours", "Renkler"),
         "desc": ("Light or dark mode, accent colour", "Açık veya koyu mod, vurgu rengi"),
         "keywords": "accent color colour dark light mode theme vurgu renk koyu açık tema"},
        {"id": "lockscreen", "icon": "system-lock-screen", "kcm": "kcm_screenlocker",
         "title": ("Lock screen", "Kilit ekranı"),
         "desc": ("When to lock, lock screen picture", "Ne zaman kilitleneceği, kilit ekranı resmi"),
         "keywords": "lock password kilit parola"},
        {"id": "fonts", "icon": "preferences-desktop-font", "kcm": "kcm_fonts",
         "title": ("Fonts", "Yazı tipleri"),
         "desc": ("Text size and fonts", "Yazı boyutu ve yazı tipleri"),
         "keywords": "text size font yazı boyutu"},
        {"id": "cursor", "icon": "preferences-cursors", "kcm": "kcm_cursortheme",
         "title": ("Mouse pointer", "Fare işaretçisi"),
         "desc": ("Pointer style and size", "İşaretçi stili ve boyutu"),
         "keywords": "cursor pointer imleç"},
    ]},
    {"id": "apps", "icon": "applications-all", "title": ("Apps", "Uygulamalar"), "items": [
        {"id": "windows-apps", "icon": "application-x-ms-dos-executable", "page": "windows-apps",
         "title": ("Windows programs", "Windows programları"),
         "desc": ("Programs installed from .exe and .msi files", ".exe ve .msi dosyalarından kurulan programlar"),
         "keywords": "exe msi wine windows uninstall kaldır program"},
        {"id": "store", "icon": "veltos-store", "action": "store",
         "title": ("Get apps from the Store", "Mağazadan uygulama edinin"),
         "desc": ("Install and remove apps", "Uygulama kurma ve kaldırma"),
         "keywords": "install remove uninstall software discover kur kaldır yazılım mağaza"},
        {"id": "defaultapps", "icon": "preferences-desktop-default-applications", "kcm": "kcm_componentchooser",
         "title": ("Default apps", "Varsayılan uygulamalar"),
         "desc": ("Web browser, email, file manager", "Web tarayıcısı, e-posta, dosya yöneticisi"),
         "keywords": "browser default open with tarayıcı varsayılan"},
        {"id": "filetypes", "icon": "preferences-desktop-filetype-association", "kcm": "kcm_filetypes",
         "title": ("Open files with", "Dosyaları şununla aç"),
         "desc": ("Which app opens which file type", "Hangi dosya türünü hangi uygulamanın açacağı"),
         "keywords": "file association extension dosya türü uzantı"},
        {"id": "startup", "icon": "system-run", "kcm": "kcm_autostart",
         "title": ("Startup", "Başlangıç"),
         "desc": ("Apps that start when you sign in", "Oturum açınca başlayan uygulamalar"),
         "keywords": "autostart login boot başlangıç"},
    ]},
    {"id": "accounts", "icon": "user-identity", "title": ("Accounts", "Hesaplar"), "items": [
        {"id": "users", "icon": "user-identity", "kcm": "kcm_users",
         "title": ("Your info & other users", "Bilgileriniz ve diğer kullanıcılar"),
         "desc": ("Name, picture, password, add a user", "Ad, resim, parola, kullanıcı ekleme"),
         "keywords": "user password account picture kullanıcı parola hesap"},
    ]},
    {"id": "time", "icon": "clock", "title": ("Time & language", "Saat ve dil"), "items": [
        {"id": "datetime", "icon": "preferences-system-time", "page": "datetime",
         "title": ("Date & time", "Tarih ve saat"),
         "desc": ("Time zone, set the time automatically", "Saat dilimi, saati otomatik ayarlama"),
         "keywords": "clock timezone ntp saat dilimi"},
        {"id": "region", "icon": "preferences-desktop-locale", "kcm": "kcm_regionandlang",
         "title": ("Language & region", "Dil ve bölge"),
         "desc": ("Display language, formats", "Görüntü dili, biçimler"),
         "keywords": "language locale format türkçe english dil biçim"},
        {"id": "typing", "icon": "input-keyboard", "kcm": "kcm_keyboard",
         "title": ("Typing", "Yazma"),
         "desc": ("Keyboard layouts", "Klavye düzenleri"),
         "keywords": "layout keyboard klavye"},
        {"id": "spelling", "icon": "tools-check-spelling", "kcm": "kcmspellchecking",
         "title": ("Spelling", "Yazım denetimi"),
         "desc": ("Spell checking languages", "Yazım denetimi dilleri"),
         "keywords": "spell check yazım"},
    ]},
    {"id": "gaming", "icon": "input-gaming", "title": ("Gaming", "Oyun"), "items": [
        {"id": "gamecontrollers", "icon": "input-gaming", "kcm": "kcm_gamecontroller",
         "title": ("Game controllers", "Oyun kumandaları"),
         "desc": ("Test and set up gamepads and joysticks", "Gamepad ve joystick testi ve ayarı"),
         "keywords": "gamepad joystick controller kumanda"},
        {"id": "graphics", "icon": "video-display", "page": "about",
         "title": ("Graphics", "Grafik"),
         "desc": ("Your graphics card", "Ekran kartınız"),
         "keywords": "gpu graphics card nvidia amd intel ekran kartı"},
    ]},
    {"id": "accessibility", "icon": "preferences-desktop-accessibility-symbolic", "title": ("Accessibility", "Erişilebilirlik"), "items": [
        {"id": "access", "icon": "preferences-desktop-accessibility", "kcm": "kcm_access",
         "title": ("Accessibility", "Erişilebilirlik"),
         "desc": ("Sticky keys, visual bell, screen reader", "Yapışkan tuşlar, görsel uyarı, ekran okuyucu"),
         "keywords": "screen reader sticky keys bell ekran okuyucu"},
        {"id": "virtualkeyboard", "icon": "input-keyboard-virtual", "kcm": "kcm_virtualkeyboard",
         "title": ("On-screen keyboard", "Ekran klavyesi"),
         "desc": ("Keyboard on the screen for touch use", "Dokunmatik kullanım için ekran klavyesi"),
         "keywords": "virtual keyboard sanal klavye"},
        {"id": "textsize", "icon": "preferences-desktop-font", "kcm": "kcm_fonts",
         "title": ("Text size", "Yazı boyutu"),
         "desc": ("Make text bigger", "Yazıları büyütme"),
         "keywords": "font size bigger zoom büyüt"},
    ]},
    {"id": "privacy", "icon": "security-high", "title": ("Privacy & security", "Gizlilik ve güvenlik"), "items": [
        {"id": "lock", "icon": "system-lock-screen", "kcm": "kcm_screenlocker",
         "title": ("Screen lock", "Ekran kilidi"),
         "desc": ("Lock automatically, ask for the password", "Otomatik kilitleme, parola sorma"),
         "keywords": "lock password kilit"},
        {"id": "firewall2", "icon": "security-high", "kcm": "kcm_firewall",
         "title": ("Firewall", "Güvenlik duvarı"),
         "desc": ("Allow or block network connections", "Ağ bağlantılarına izin verme veya engelleme"),
         "keywords": "firewall security güvenlik"},
        {"id": "recent", "icon": "document-open-recent", "kcm": "kcm_recentFiles",
         "title": ("Activity history", "Etkinlik geçmişi"),
         "desc": ("Remember recently used files", "Son kullanılan dosyaları hatırlama"),
         "keywords": "history recent files geçmiş son dosyalar"},
        {"id": "search", "icon": "system-search", "kcm": "kcm_baloofile",
         "title": ("Searching files", "Dosya arama"),
         "desc": ("Which folders search indexes", "Aramanın hangi klasörleri dizinlediği"),
         "keywords": "index search arama dizin"},
    ]},
    {"id": "update", "icon": "view-refresh", "title": ("VeltOS Update", "VeltOS Güncelleme"), "items": [
        {"id": "updates", "icon": "system-software-update", "action": "updates",
         "title": ("Check for updates", "Güncellemeleri denetle"),
         "desc": ("Security fixes and app updates", "Güvenlik düzeltmeleri ve uygulama güncellemeleri"),
         "keywords": "update upgrade patch security güncelleme yama güvenlik"},
    ]},
]


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
        "kcm": item.get("kcm", ""),
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
