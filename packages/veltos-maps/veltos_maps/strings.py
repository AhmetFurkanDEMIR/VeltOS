"""VeltOS Maps' English and Turkish user interface text."""

import os

TEXTS = {
    "app_title": ("Maps", "Haritalar"),
    "search_placeholder": ("Search for a place", "Yer arayın"),
    "search": ("Search", "Ara"),
    "location_on": ("Location on", "Konum açık"),
    "location_off": ("Location off", "Konum kapalı"),
    "location_on_tip": ("Location access is on. Select to turn it off.",
                        "Konum erişimi açık. Kapatmak için seçin."),
    "location_off_tip": ("Location access is off. Select to turn it on.",
                         "Konum erişimi kapalı. Açmak için seçin."),
    "location_hint": ("Turn location access on or off", "Konum erişimini açın veya kapatın"),
    "location_turned_on": ("Location access is on. Select My location to see where you are.",
                           "Konum erişimi açık. Nerede olduğunuzu görmek için Konumum'u seçin."),
    "location_turned_off": ("Location access is off.", "Konum erişimi kapalı."),
    "my_location": ("My location", "Konumum"),
    "settings": ("Location settings", "Konum ayarları"),
    "privacy_note": ("Maps shows Google Maps. Your searches and the places you look at go to Google; your "
                     "location only when you select My location.",
                     "Haritalar, Google Haritalar'ı gösterir. Aramalarınız ve baktığınız yerler Google'a gider; "
                     "konumunuz yalnızca Konumum'u seçtiğinizde."),
    "got_it": ("Got it", "Anladım"),
    "close": ("Close", "Kapat"),
    "location_error": ("Couldn't read or change the location setting: {error}",
                       "Konum ayarı okunamadı veya değiştirilemedi: {error}"),
    "location_disabled": ("Turn on location access to use My location.",
                          "Konumum'u kullanmak için konum erişimini açın."),
    "location_progress": ("Finding your location…", "Konumunuz bulunuyor…"),
    "location_failed": ("We couldn't find your location. Set a default location to use when this PC can't "
                        "find it.",
                        "Konumunuz bulunamadı. Bu bilgisayar konumu bulamadığında kullanılacak bir varsayılan "
                        "konum ayarlayın."),
    "location_default_shown": ("This PC couldn't find your location, so Maps shows your default location.",
                               "Bu bilgisayar konumunuzu bulamadı; Haritalar varsayılan konumunuzu gösteriyor."),
    "location_ready": ("Showing your current location.", "Mevcut konumunuz gösteriliyor."),
    "show_default": ("Show my default location", "Varsayılan konumumu göster"),
    "set_default_title": ("Set your default location", "Varsayılan konumunuzu ayarlayın"),
    "set_default_desc": ("Move the map so your home or office is in the middle, then select Set as default "
                         "location.",
                         "Haritayı evinizi veya ofisinizi ortaya alacak şekilde kaydırın, ardından Varsayılan "
                         "konum olarak ayarla'yı seçin."),
    "set_default_button": ("Set as default location", "Varsayılan konum olarak ayarla"),
    "default_move_map": ("Move or zoom the map a little first, so Maps knows its centre.",
                         "Önce haritayı biraz kaydırın veya yakınlaştırın; Haritalar merkezi böylece öğrenir."),
    "default_save_failed": ("The default location couldn't be saved.", "Varsayılan konum kaydedilemedi."),
    "default_saved": ("Your default location is saved.", "Varsayılan konumunuz kaydedildi."),
    "offline_title": ("Can't reach Google Maps", "Google Haritalar'a ulaşılamıyor"),
    "offline_desc": ("Maps needs an internet connection. Check that this PC is online, then try again.",
                     "Haritalar internet bağlantısı gerektirir. Bu bilgisayarın çevrimiçi olduğunu denetleyip "
                     "yeniden deneyin."),
    "retry": ("Try again", "Yeniden dene"),
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
