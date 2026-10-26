"""VeltOS Maps' English and Turkish user interface text."""

import os

TEXTS = {
    "app_title": ("Maps", "Haritalar"),
    "search_placeholder": ("Search for a place", "Yer arayın"),
    "search": ("Search", "Ara"),
    "location_on": ("Location on", "Konum açık"),
    "location_off": ("Location off", "Konum kapalı"),
    "location_hint": ("Turn location access on or off", "Konum erişimini açın veya kapatın"),
    "my_location": ("My location", "Konumum"),
    "settings": ("Location settings", "Konum ayarları"),
    "privacy_note": ("Google Maps needs an internet connection. Your searches are sent to Google.",
                     "Google Haritalar internet bağlantısı gerektirir. Aramalarınız Google'a gönderilir."),
    "location_error": ("Couldn't read or change the location setting: {error}",
                       "Konum ayarı okunamadı veya değiştirilemedi: {error}"),
    "location_disabled": ("Turn on location access in Settings before requesting your location.",
                          "Konumunuzu istemeden önce Ayarlar'dan konum erişimini açın."),
    "location_progress": ("Finding your location…", "Konumunuz bulunuyor…"),
    "location_failed": ("Couldn't get your location: {error}",
                        "Konumunuz alınamadı: {error}"),
    "location_ready": ("Showing your current location.", "Mevcut konumunuz gösteriliyor."),
    "settings_error": ("Couldn't open Location settings: {error}",
                       "Konum ayarları açılamadı: {error}"),
    "open_failed": ("Couldn't open the link in your browser.", "Bağlantı tarayıcınızda açılamadı."),
}


def language():
    for key in ("LANGUAGE", "LC_MESSAGES", "LANG"):
        value = os.environ.get(key, "").split(":", 1)[0].split(".", 1)[0]
        if value.lower().startswith("tr"):
            return "tr"
        if value:
            return "en"
    return "en"


def text(lang, key, **values):
    value = TEXTS[key][1 if lang == "tr" else 0]
    return value.format(**values) if values else value
