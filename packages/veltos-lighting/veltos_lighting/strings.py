"""Texts of VeltOS Keyboard Lighting (English, Turkish), in the words of
Windows 11's Dynamic Lighting where it has them."""

import os

TEXTS = {
    "app_title": ("Keyboard Lighting", "Klavye Aydınlatması"),
    "subtitle": ("Turn your keyboard's lights on or off and choose their brightness and colour",
                 "Klavyenizin ışıklarını açın veya kapatın; parlaklığını ve rengini seçin"),
    "keyboard": ("Keyboard", "Klavye"),
    "built_in": ("Built-in keyboard", "Yerleşik klavye"),
    "one_colour": ("One colour: brightness only", "Tek renk: yalnızca parlaklık"),
    "rgb": ("Colour lighting", "Renkli aydınlatma"),
    "lighting": ("Lighting", "Aydınlatma"),
    "lighting_desc": ("Turn the keyboard's lights on or off", "Klavye ışıklarını açın veya kapatın"),
    "on": ("On", "Açık"),
    "off": ("Off", "Kapalı"),
    "brightness": ("Brightness", "Parlaklık"),
    "effects": ("Effects", "Efektler"),
    "effects_desc": ("Choose how the lights look", "Işıkların nasıl görüneceğini seçin"),
    "effect_static": ("Solid colour", "Düz renk"),
    "effect_breathing": ("Breathing", "Nefes alma"),
    "effect_cycle": ("Colour cycle", "Renk döngüsü"),
    "speed": ("Effect speed", "Efekt hızı"),
    "speed_0": ("Slow", "Yavaş"),
    "speed_1": ("Medium", "Orta"),
    "speed_2": ("Fast", "Hızlı"),
    "match_accent": ("Match my accent colour", "Vurgu rengimle eşleştir"),
    "match_accent_desc": ("The keyboard takes the accent colour of Personalization > Colours",
                          "Klavye, Kişiselleştirme > Renkler'deki vurgu rengini alır"),
    "colour": ("Colour", "Renk"),
    "custom_colour": ("Custom colour", "Özel renk"),
    "hue": ("Hue", "Ton"),
    "none_title": ("No keyboard lighting was found", "Klavye aydınlatması bulunamadı"),
    "none_text": ("This PC's keyboard has no lights VeltOS can control. Laptops whose keyboard lights up "
                  "show it here (ThinkPad, Dell, HP, Lenovo, ASUS, MSI, System76 and others). Keyboards "
                  "with their own controller (USB gaming keyboards) need their maker's app.",
                  "Bu bilgisayarın klavyesinde VeltOS'un denetleyebileceği ışık yok. Klavyesi ışıklı "
                  "dizüstü bilgisayarlar burada görünür (ThinkPad, Dell, HP, Lenovo, ASUS, MSI, System76 ve "
                  "diğerleri). Kendi denetleyicisi olan klavyeler (USB oyun klavyeleri) üreticisinin "
                  "uygulamasını ister."),
    "failed": ("The keyboard lighting could not be changed.", "Klavye aydınlatması değiştirilemedi."),
    "refresh": ("Refresh", "Yenile"),
    "settings_row": ("Keyboard lighting", "Klavye aydınlatması"),
}


def language(environ=None):
    environ = os.environ if environ is None else environ
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = environ.get(variable, "")
        if value:
            return "tr" if value.split(":")[0].lower().startswith("tr") else "en"
    return "en"


def texts(lang):
    index = 1 if lang == "tr" else 0
    return {key: pair[index] for key, pair in TEXTS.items()}
