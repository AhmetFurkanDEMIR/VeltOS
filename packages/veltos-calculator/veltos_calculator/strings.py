"""Texts of VeltOS Calculator (English, Turkish), in Windows 11 wording."""

import os

TEXTS = {
    "app_title": ("Calculator", "Hesap Makinesi"),
    "standard": ("Standard", "Standart"),
    "scientific": ("Scientific", "Bilimsel"),
    "calculator": ("Calculator", "Hesap Makinesi"),
    "settings": ("Settings", "Ayarlar"),
    "open_navigation": ("Open Navigation", "Gezintiyi aç"),
    "close_navigation": ("Close Navigation", "Gezintiyi kapat"),
    "history": ("History", "Geçmiş"),
    "memory": ("Memory", "Bellek"),
    "no_history": ("There's no history yet", "Henüz geçmiş yok"),
    "no_memory": ("There's nothing saved in memory", "Bellekte kayıtlı bir şey yok"),
    "clear_history": ("Clear all history", "Tüm geçmişi temizle"),
    "clear_memory": ("Clear all memory", "Tüm belleği temizle"),
    "keep_on_top": ("Keep on top", "Üstte tut"),
    "back_to_full": ("Back to full view", "Tam görünüme dön"),
    "memory_clear": ("Clear memory item", "Bellek öğesini temizle"),
    "memory_add": ("Add to memory item", "Bellek öğesine ekle"),
    "memory_subtract": ("Subtract from memory item", "Bellek öğesinden çıkar"),
    "trigonometry": ("Trigonometry", "Trigonometri"),
    "function": ("Function", "Fonksiyon"),
    "divide_by_zero": ("Cannot divide by zero", "Sıfıra bölünemez"),
    "undefined": ("Result is undefined", "Sonuç tanımsız"),
    "overflow": ("Overflow", "Taşma"),
    "invalid_input": ("Invalid input", "Geçersiz giriş"),
    "copy": ("Copy", "Kopyala"),
    "paste": ("Paste", "Yapıştır"),
    "appearance": ("Appearance", "Görünüm"),
    "app_theme": ("App theme", "Uygulama teması"),
    "app_theme_hint": ("Select which app theme to display", "Görüntülenecek uygulama temasını seçin"),
    "theme_light": ("Light", "Açık"),
    "theme_dark": ("Dark", "Koyu"),
    "theme_system": ("Use system setting", "Sistem ayarını kullan"),
    "about": ("About", "Hakkında"),
    "about_name": ("VeltOS Calculator", "VeltOS Hesap Makinesi"),
    "about_text": ("Standard and scientific calculator in the style of Windows 11. "
                   "Decimal arithmetic: 0.1 + 0.2 is exactly 0.3.",
                   "Windows 11 tarzında standart ve bilimsel hesap makinesi. "
                   "Ondalık aritmetik: 0,1 + 0,2 tam olarak 0,3'tür."),
    "copyright": ("© 2026 VeltOS Developers", "© 2026 VeltOS Geliştiricileri"),
}


def language():
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable, "")
        if value:
            return "tr" if value.split(":")[0].startswith("tr") else "en"
    return "en"


def texts(lang):
    index = 1 if lang == "tr" else 0
    return {key: pair[index] for key, pair in TEXTS.items()}
