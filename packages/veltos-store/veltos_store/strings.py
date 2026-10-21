"""Texts of VeltOS Store (English, Turkish), in Microsoft Store wording."""

import os

TEXTS = {
    "app_title": ("VeltOS Store", "VeltOS Mağaza"),
    "home": ("Home", "Giriş"),
    "apps": ("Apps", "Uygulamalar"),
    "games": ("Gaming", "Oyun"),
    "library": ("Library", "Kitaplık"),
    "search": ("Search apps and games", "Uygulama ve oyun arayın"),
    "loading": ("Loading the catalogue…", "Katalog yükleniyor…"),
    "no_catalog": ("The app catalogue is not available. Connect to the internet and try again later.",
                   "Uygulama kataloğu kullanılamıyor. İnternete bağlanıp daha sonra yeniden deneyin."),
    "featured": ("Featured", "Öne çıkanlar"),
    "see_details": ("See details", "Ayrıntıları gör"),
    "essentials": ("Essential apps", "Temel uygulamalar"),
    "top_productivity": ("Productivity", "Verimlilik"),
    "top_creative": ("Create and edit", "Oluşturun ve düzenleyin"),
    "top_games": ("Top free games", "En iyi ücretsiz oyunlar"),
    "see_all": ("See all", "Tümünü gör"),
    "free": ("Free", "Ücretsiz"),
    "installed": ("Installed", "Yüklü"),
    "install": ("Install", "Yükle"),
    "open": ("Open", "Aç"),
    "uninstall": ("Uninstall", "Kaldır"),
    "cancel": ("Cancel", "İptal"),
    "waiting": ("Pending", "Bekliyor"),
    "installing": ("Installing", "Yükleniyor"),
    "removing": ("Uninstalling", "Kaldırılıyor"),
    "updating": ("Updating", "Güncelleştiriliyor"),
    "authorising": ("Waiting for your permission", "İzniniz bekleniyor"),
    "downloading": ("Downloading", "İndiriliyor"),
    "failed": ("Something went wrong. Try again.", "Bir sorun oluştu. Yeniden deneyin."),
    # What went wrong, from PackageKit's message (packages.failure_key).
    "failed_auth": ("Permission was not given. Enter the administrator password to install.",
                    "İzin verilmedi. Yüklemek için yönetici parolasını girin."),
    "failed_not_found": ("This app is not in the catalogue right now. Check for updates and try again.",
                         "Bu uygulama şu anda katalogda yok. Güncelleştirmeleri denetleyip yeniden deneyin."),
    "failed_network": ("The download failed. Check your internet connection and try again.",
                       "İndirme başarısız oldu. İnternet bağlantınızı denetleyip yeniden deneyin."),
    "failed_busy": ("Another installation is running. Wait for it to finish and try again.",
                    "Başka bir yükleme sürüyor. Bitmesini bekleyip yeniden deneyin."),
    "failed_detail": ("Something went wrong: {detail}", "Bir sorun oluştu: {detail}"),
    "refreshing": ("Checking the catalogue", "Katalog denetleniyor"),
    "results_for": ("Results for “%1”", "“%1” için sonuçlar"),
    "no_results": ("No results. Try a different word.", "Sonuç yok. Başka bir sözcük deneyin."),
    "all_categories": ("All", "Tümü"),
    "screenshots": ("Screenshots", "Ekran görüntüleri"),
    "description": ("Description", "Açıklama"),
    "more_info": ("Additional information", "Ek bilgiler"),
    "published_by": ("Published by", "Yayımlayan"),
    "category": ("Category", "Kategori"),
    "package": ("Package", "Paket"),
    "license": ("License", "Lisans"),
    "website": ("Website", "Web sitesi"),
    "unknown_developer": ("Community", "Topluluk"),
    "updates": ("Updates & downloads", "Güncelleştirmeler ve indirmeler"),
    "get_updates": ("Get updates", "Güncelleştirmeleri al"),
    "checking": ("Checking for updates…", "Güncelleştirmeler denetleniyor…"),
    "up_to_date": ("You're up to date", "Güncelsiniz"),
    "updates_available": ("%1 updates available", "%1 güncelleştirme var"),
    "update_all": ("Update all", "Tümünü güncelleştir"),
    "installed_apps": ("Installed apps", "Yüklü uygulamalar"),
    "no_installed": ("Apps you install from the Store show here.",
                     "Mağaza'dan yüklediğiniz uygulamalar burada görünür."),
    "back": ("Back", "Geri"),
    "protected": ("This app is part of VeltOS and can't be uninstalled.",
                  "Bu uygulama VeltOS'un bir parçası, kaldırılamaz."),
    "windows_apps_note": ("Windows programs (.exe, .msi) install with a double-click in File Explorer.",
                          "Windows programları (.exe, .msi) Dosya Gezgini'nde çift tıklanarak yüklenir."),
}


def language(environ=None):
    environ = os.environ if environ is None else environ
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = environ.get(variable)
        if value:
            return "tr" if value.lower().startswith("tr") else "en"
    return "en"


def texts(lang):
    index = 1 if lang == "tr" else 0
    return {key: values[index] for key, values in TEXTS.items()}
