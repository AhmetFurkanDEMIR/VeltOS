"""Texts of VeltOS Notepad in English and Turkish (Windows 11 Notepad's
wording)."""

import os

TEXTS = {
    "app_title": ("Notepad", "Not Defteri"),
    "untitled": ("Untitled", "Adsız"),
    # Menus
    "file": ("File", "Dosya"),
    "edit": ("Edit", "Düzenle"),
    "view": ("View", "Görünüm"),
    "settings": ("Settings", "Ayarlar"),
    "new_tab": ("New tab", "Yeni sekme"),
    "new_window": ("New window", "Yeni pencere"),
    "open": ("Open", "Aç"),
    "recent": ("Recent", "En son"),
    "no_recent": ("No recent files", "Son dosya yok"),
    "save": ("Save", "Kaydet"),
    "save_as": ("Save as", "Farklı kaydet"),
    "save_all": ("Save all", "Tümünü kaydet"),
    "print": ("Print", "Yazdır"),
    "close_tab": ("Close tab", "Sekmeyi kapat"),
    "close_window": ("Close window", "Pencereyi kapat"),
    "exit": ("Exit", "Çıkış"),
    "undo": ("Undo", "Geri al"),
    "redo": ("Redo", "Yinele"),
    "cut": ("Cut", "Kes"),
    "copy": ("Copy", "Kopyala"),
    "paste": ("Paste", "Yapıştır"),
    "delete": ("Delete", "Sil"),
    "find": ("Find", "Bul"),
    "find_next": ("Find next", "Sonrakini bul"),
    "find_previous": ("Find previous", "Öncekini bul"),
    "replace": ("Replace", "Değiştir"),
    "replace_all": ("Replace all", "Tümünü değiştir"),
    "go_to": ("Go to", "Git"),
    "select_all": ("Select all", "Tümünü seç"),
    "time_date": ("Time/Date", "Saat/Tarih"),
    "font": ("Font", "Yazı tipi"),
    "zoom": ("Zoom", "Yakınlaştır"),
    "zoom_in": ("Zoom in", "Yakınlaştır"),
    "zoom_out": ("Zoom out", "Uzaklaştır"),
    "zoom_reset": ("Restore default zoom", "Varsayılan yakınlaştırmayı geri yükle"),
    "status_bar": ("Status bar", "Durum çubuğu"),
    "word_wrap": ("Word wrap", "Sözcük kaydırma"),
    # Window
    "minimize": ("Minimize", "Simge durumuna küçült"),
    "maximize": ("Maximize", "Ekranı kapla"),
    "restore_down": ("Restore down", "Önceki boyut"),
    "close": ("Close", "Kapat"),
    "add_tab": ("Add new tab", "Yeni sekme ekle"),
    # Status bar
    "line_column": ("Ln {line}, Col {column}", "Satır {line}, Sütun {column}"),
    "characters": ("{count} characters", "{count} karakter"),
    "one_character": ("1 character", "1 karakter"),
    "selected_of": ("{selected} of {count} characters", "{selected}/{count} karakter"),
    "eol_CRLF": ("Windows (CRLF)", "Windows (CRLF)"),
    "eol_LF": ("Unix (LF)", "Unix (LF)"),
    "eol_CR": ("Macintosh (CR)", "Macintosh (CR)"),
    "line_ending": ("Line ending", "Satır sonu"),
    "encoding": ("Encoding", "Kodlama"),
    # Find and replace
    "find_placeholder": ("Find", "Bul"),
    "replace_placeholder": ("Replace", "Değiştir"),
    "match_case": ("Match case", "Büyük/küçük harf eşleştir"),
    "wrap_around": ("Wrap around", "Başa dön"),
    "toggle_replace": ("Toggle replace", "Değiştirmeyi aç/kapat"),
    "options": ("Options", "Seçenekler"),
    "not_found": ("Cannot find “{text}”", "“{text}” bulunamıyor"),
    "replaced": ("Replaced {count} occurrences", "{count} yerde değiştirildi"),
    # Dialogs
    "save_changes": ("Do you want to save changes to {name}?",
                     "{name} dosyasındaki değişiklikleri kaydetmek istiyor musunuz?"),
    "dont_save": ("Don't save", "Kaydetme"),
    "cancel": ("Cancel", "İptal"),
    "go_to_line": ("Go to line", "Satıra git"),
    "line_number": ("Line number", "Satır numarası"),
    "ok": ("OK", "Tamam"),
    "cant_open": ("Notepad can't open “{name}”. It may be too large, a folder, or you may "
                  "not have permission to read it.",
                  "Not Defteri “{name}” dosyasını açamıyor. Dosya çok büyük ya da bir klasör "
                  "olabilir veya okuma izniniz olmayabilir."),
    "cant_save": ("Notepad can't save “{name}”. You may not have permission to change "
                  "this location. Try “Save as”.",
                  "Not Defteri “{name}” dosyasını kaydedemiyor. Bu konumu değiştirme "
                  "izniniz olmayabilir. “Farklı kaydet” seçeneğini deneyin."),
    "binary_file": ("“{name}” does not look like a text file; some characters may not show "
                    "correctly.",
                    "“{name}” bir metin dosyasına benzemiyor; bazı karakterler doğru "
                    "görünmeyebilir."),
    "text_files": ("Text documents", "Metin belgeleri"),
    "all_files": ("All files", "Tüm dosyalar"),
    # Settings page
    "app_theme": ("App theme", "Uygulama teması"),
    "app_theme_desc": ("Select which app theme to display", "Görüntülenecek uygulama temasını seçin"),
    "theme_light": ("Light", "Açık"),
    "theme_dark": ("Dark", "Koyu"),
    "theme_system": ("Use system setting", "Sistem ayarını kullan"),
    "font_family": ("Family", "Aile"),
    "font_style": ("Style", "Stil"),
    "font_size": ("Size", "Boyut"),
    "style_regular": ("Regular", "Normal"),
    "style_italic": ("Italic", "İtalik"),
    "style_bold": ("Bold", "Kalın"),
    "style_bold_italic": ("Bold Italic", "Kalın İtalik"),
    "font_preview": ("The quick brown fox jumps over the lazy dog.",
                     "Pijamalı hasta yağız şoföre çabucak güvendi."),
    "text_formatting": ("Text formatting", "Metin biçimlendirme"),
    "word_wrap_desc": ("Fit text within the window by default", "Metni varsayılan olarak pencereye sığdır"),
    "opening_notepad": ("Opening Notepad", "Not Defteri'ni açma"),
    "opening_files": ("Opening files", "Dosyaları açma"),
    "open_in_tab": ("Open in a new tab", "Yeni sekmede aç"),
    "open_in_window": ("Open in a new window", "Yeni pencerede aç"),
    "when_starts": ("When Notepad starts", "Not Defteri başlatıldığında"),
    "continue_session": ("Continue previous session", "Önceki oturuma devam et"),
    "new_session": ("Start new session and discard unsaved changes",
                    "Yeni oturum başlat ve kaydedilmemiş değişiklikleri at"),
    "about_this_app": ("About this app", "Bu uygulama hakkında"),
    "about_text": ("Notepad for VeltOS, in the look of Windows 11 Notepad. Version {version}.",
                   "VeltOS için Not Defteri, Windows 11 Not Defteri görünümünde. Sürüm {version}."),
    "back": ("Back", "Geri"),
}


def language(environ=None):
    environ = os.environ if environ is None else environ
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = environ.get(variable)
        if value:
            return "tr" if value.lower().startswith("tr") else "en"
    return "en"


def texts(lang):
    i = 1 if lang == "tr" else 0
    return {key: pair[i] for key, pair in TEXTS.items()}
