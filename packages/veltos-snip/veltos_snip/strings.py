"""Texts of VeltOS Snipping Tool (English, Turkish), in Windows 11 wording."""

import os

TEXTS = {
    "app_title": ("Snipping Tool", "Ekran Alıntısı Aracı"),
    "new": ("New", "Yeni"),
    "empty": ("Press Windows logo key + Shift + S to start a snip.",
              "Ekran alıntısı başlatmak için Windows logo tuşu + Shift + S tuşlarına basın."),
    "empty_hint": ("Or press Print Screen. Snips are copied to the clipboard and saved in Pictures > Screenshots.",
                   "Ya da Print Screen tuşuna basın. Alıntılar panoya kopyalanır ve Resimler > Screenshots "
                   "klasörüne kaydedilir."),
    "mode_rect": ("Rectangle", "Dikdörtgen"),
    "mode_window": ("Window", "Pencere"),
    "mode_full": ("Full screen", "Tam ekran"),
    "mode_free": ("Freeform", "Serbest biçim"),
    "no_delay": ("No delay", "Gecikme yok"),
    "delay_3": ("3 seconds", "3 saniye"),
    "delay_5": ("5 seconds", "5 saniye"),
    "delay_10": ("10 seconds", "10 saniye"),
    "close": ("Close", "Kapat"),
    "pen": ("Ballpoint pen", "Tükenmez kalem"),
    "highlighter": ("Highlighter", "Vurgulayıcı"),
    "eraser": ("Eraser", "Silgi"),
    "crop": ("Image crop", "Resmi kırp"),
    "undo": ("Undo", "Geri al"),
    "redo": ("Redo", "Yinele"),
    "save": ("Save", "Kaydet"),
    "copy": ("Copy", "Kopyala"),
    "apply": ("Apply", "Uygula"),
    "cancel": ("Cancel", "İptal"),
    "saved": ("Saved to Pictures > Screenshots", "Resimler > Screenshots klasörüne kaydedildi"),
    "show_in_folder": ("Show in folder", "Klasörde göster"),
    "copied": ("Copied to the clipboard", "Panoya kopyalandı"),
    "auto_save": ("Automatically save snips", "Alıntıları otomatik kaydet"),
    "toast_title": ("Snip copied to clipboard", "Ekran alıntısı panoya kopyalandı"),
    "toast_body": ("Select here to mark up and share the image.",
                   "Görüntüye not eklemek ve paylaşmak için burayı seçin."),
    "toast_action": ("Mark up and share", "Not ekle ve paylaş"),
    "capture_failed": ("The screen could not be captured.", "Ekran görüntüsü alınamadı."),
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
