"""Short commands VeltOS AI recognises itself, in Turkish and English, for
the local model: "Koyu moda geç", "Wi-Fi'ı kapat", "Hesap makinesini aç",
"parlaklığı %40 yap", "turn off bluetooth"...

The 2B local model picked the right action for most such commands but
not all (out/ai-test, 2026-10-27: "Koyu moda geç" asked for a screenshot,
"Hesap makinesini aç" opened an app called "VeltOS"), and these are the
requests the product owner names first. A command that matches here
becomes the action directly (the panel still asks "Allow" for every
change); the model then only words the answer. Anything else, and every
request to the online services, goes to the model as before.

match(text, lang) returns (tool name, arguments) or None. Only short
messages (up to eight words) are read as commands.
"""

import re

from . import tools

ON = r"(aç|açın|açar mısın|etkinleştir|başlat|on|enable|turn on|switch on)"
OFF = r"(kapat|kapatın|kapatır mısın|devre dışı bırak|off|disable|turn off|switch off)"


def fold(text):
    """Lower case the Turkish way (İ -> i, I -> ı), without apostrophes and
    punctuation at the ends."""
    text = text.replace("İ", "i").replace("I", "ı").lower()
    text = re.sub(r"[’'`´]", "", text)
    text = re.sub(r"[.!?,;:]+", " ", text)
    return " ".join(text.split())


def english_fold(text):
    """Lower case as in English (for English app names)."""
    return " ".join(re.sub(r"[.!?,;:’'`´]+", " ", text).lower().split())


# Turkish case endings an app name may carry before "aç": "Hesap
# makinesini", "Not Defteri'ni", "Firefox'u".
SUFFIXES = ("nı", "ni", "nu", "nü", "yı", "yi", "yu", "yü", "ı", "i", "u", "ü")


def name_forms(name):
    forms = [name]
    for suffix in SUFFIXES:
        if name.endswith(suffix) and len(name) - len(suffix) >= 3:
            forms.append(name[: -len(suffix)])
    return forms


def toggle(text, words):
    """True (on), False (off) or None for "<words> ... aç/kapat" in either order."""
    if not re.search(words, text):
        return None
    if re.search(rf"(^|\s){OFF}(\s|$)", text) or re.search(r"\bkapa\w*", text):
        return False
    if re.search(rf"(^|\s){ON}(\s|$)", text) or re.search(r"\baç\w*", text):
        return True
    return None


def number(text):
    match = re.search(r"(\d{1,3})", text)
    return max(0, min(100, int(match.group(1)))) if match else None


def match(text, lang="en", find_app=tools.find_app):
    folded = fold(text)
    if not folded or len(folded.split()) > 8:
        return None
    # A question ("Wi-Fi açık mı?", "is Bluetooth on?") is for the model.
    if "?" in text or re.search(r"\s(mı|mi|mu|mü)(\s|$)", folded) or folded.startswith(("is ", "are ", "what ")):
        return None
    # Light and dark mode.
    if re.search(r"(koyu|karanlık|siyah|dark)\s*(mod|tema|görünüm|mode|theme)", folded) \
            or re.search(r"(mode|theme)\s+(to\s+)?dark", folded):
        return "set_theme", {"mode": "dark"}
    if re.search(r"(açık|aydınlık|beyaz|light)\s*(mod|tema|görünüm|mode|theme)", folded) \
            or re.search(r"(mode|theme)\s+(to\s+)?light", folded):
        return "set_theme", {"mode": "light"}
    for words, name in ((r"wi-?fi|kablosuz", "set_wifi"), (r"bluetooth", "set_bluetooth"),
                        (r"gece ışığ|night ?light", "set_night_light"), (r"uçak mod|airplane|flight mode",
                                                                        "set_airplane_mode"),
                        (r"rahatsız etmeyin|do not disturb|dnd", "set_do_not_disturb")):
        state = toggle(folded, words)
        if state is not None:
            return name, {"on": state}
    if re.search(r"(parlaklı|brightness)", folded) and number(folded) is not None:
        return "set_brightness", {"percent": max(1, number(folded))}
    if re.search(r"\b(ses|volume)", folded) and number(folded) is not None:
        return "set_volume", {"percent": number(folded)}
    if re.fullmatch(r"(sesi kapat|sessize al|mute( the)?( sound| speakers)?)", folded):
        return "set_mute", {"muted": True}
    if re.fullmatch(r"(sesi aç|sessizden çıkar|unmute( the)?( sound| speakers)?)", folded):
        return "set_mute", {"muted": False}
    if re.search(r"güç tasarruf|pil tasarruf|power ?saver|battery saver", folded):
        return "set_power_mode", {"mode": "power-saver"}
    if re.search(r"(en iyi )?performans mod|performance mode|best performance", folded):
        return "set_power_mode", {"mode": "performance"}
    if re.search(r"dengeli( güç)? mod|balanced( power)? mode", folded):
        return "set_power_mode", {"mode": "balanced"}
    if re.search(r"(ekranı|bilgisayarı) kilitle|lock (the |my )?(screen|computer|pc)", folded):
        return "power", {"action": "lock"}
    if re.search(r"ekran görüntüsü|screenshot|ekran alıntısı", folded):
        return "take_screenshot", {}
    if re.search(r"(güncelleştirme|güncelleme)\w*\s+(yükle|kur|yap)|(sistemi|bilgisayarı)\s+güncelle|"
                 r"install (all )?updates|update (the )?(system|computer|pc)", folded):
        return "install_updates", {}
    # "<app> aç" / "open <app>".
    candidate = None
    found = re.fullmatch(r"(.+?)\s+(uygulamasını\s+)?(aç|başlat|çalıştır)", folded)
    if found:
        candidate = found.group(1)
    else:
        found = re.fullmatch(r"(open|launch|start|run)\s+(the\s+)?(.+?)(\s+app)?", english_fold(text))
        if found:
            candidate = found.group(3)
    if candidate:
        for form in name_forms(candidate):
            app = find_app(form, lang)
            if app:
                return "open_app", {"name": app[1]}
    # "<package> yükle" / "install <package>".
    found = re.fullmatch(r"([a-z0-9][a-z0-9+.-]+)(\s+(uygulamasını|programını|paketini))?\s+(yükle|kur)", folded) \
        or re.fullmatch(r"install\s+([a-z0-9][a-z0-9+.-]+)", english_fold(text))
    if found:
        return "install_app", {"package": found.group(1)}
    return None
