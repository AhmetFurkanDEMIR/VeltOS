"""Texts of VeltOS PDF Reader in English and Turkish."""

import os

TEXTS = {
    "app_title": ("PDF Reader", "PDF Okuyucu"),
    "menu": ("Menu", "Menü"),
    "home": ("Home", "Giriş"),
    "minimize": ("Minimize", "Simge durumuna küçült"),
    "maximize": ("Maximize", "Ekranı kapla"),
    "restore_down": ("Restore down", "Önceki boyut"),
    "close": ("Close", "Kapat"),
    "close_tab": ("Close tab", "Sekmeyi kapat"),
    # Home
    "welcome": ("Welcome to PDF Reader", "PDF Okuyucu'ya hoş geldiniz"),
    "welcome_text": ("Open a PDF to read, search and print it.",
                     "Okumak, aramak ve yazdırmak için bir PDF açın."),
    "open_file": ("Open file", "Dosya aç"),
    "recent": ("Recent", "Son kullanılanlar"),
    "name": ("Name", "Ad"),
    "opened": ("Opened", "Açılma"),
    "size": ("Size", "Boyut"),
    "no_recent": ("Files you open will show here.", "Açtığınız dosyalar burada görünür."),
    "remove_from_recent": ("Remove from recent", "Son kullanılanlardan kaldır"),
    "pdf_files": ("PDF files", "PDF dosyaları"),
    # Menu
    "open": ("Open", "Aç"),
    "open_recent": ("Open recent", "Son kullanılanı aç"),
    "print": ("Print", "Yazdır"),
    "properties": ("Document properties", "Belge özellikleri"),
    "show_in_folder": ("Show in folder", "Klasörde göster"),
    "read_mode": ("Read mode", "Okuma modu"),
    "full_screen": ("Full screen mode", "Tam ekran modu"),
    "exit": ("Exit", "Çıkış"),
    # Document
    "search": ("Search text", "Metin ara"),
    "find_placeholder": ("Find text in document", "Belgede metin bulun"),
    "results": ("{count} results", "{count} sonuç"),
    "one_result": ("1 result", "1 sonuç"),
    "no_results": ("No results", "Sonuç yok"),
    "page_short": ("Page {page}", "Sayfa {page}"),
    "thumbnails": ("Page thumbnails", "Sayfa küçük resimleri"),
    "bookmarks": ("Bookmarks", "Yer imleri"),
    "no_bookmarks": ("This document has no bookmarks.", "Bu belgede yer imi yok."),
    "rotate": ("Rotate view", "Görünümü döndür"),
    "zoom_in": ("Zoom in", "Yakınlaştır"),
    "zoom_out": ("Zoom out", "Uzaklaştır"),
    "fit_width": ("Fit width", "Genişliğe sığdır"),
    "fit_page": ("Fit page", "Sayfaya sığdır"),
    "previous_page": ("Previous page", "Önceki sayfa"),
    "next_page": ("Next page", "Sonraki sayfa"),
    "copy": ("Copy", "Kopyala"),
    "select_all": ("Select all", "Tümünü seç"),
    "back": ("Back", "Geri"),
    "loading": ("Opening…", "Açılıyor…"),
    "cant_open": ("PDF Reader can't open “{name}”. The file may be damaged or not a PDF.",
                  "PDF Okuyucu “{name}” dosyasını açamıyor. Dosya bozuk olabilir veya bir PDF değildir."),
    # Password
    "password_title": ("Password", "Parola"),
    "password_text": ("“{name}” is protected. Enter the document open password.",
                      "“{name}” korumalı. Belgeyi açma parolasını girin."),
    "wrong_password": ("The password is not correct. Try again.", "Parola doğru değil. Yeniden deneyin."),
    "ok": ("OK", "Tamam"),
    "cancel": ("Cancel", "İptal"),
    # Properties
    "description": ("Description", "Açıklama"),
    "file": ("File", "Dosya"),
    "title": ("Title", "Başlık"),
    "author": ("Author", "Yazar"),
    "subject": ("Subject", "Konu"),
    "keywords": ("Keywords", "Anahtar sözcükler"),
    "created": ("Created", "Oluşturulma"),
    "modified": ("Modified", "Değiştirilme"),
    "application": ("Application", "Uygulama"),
    "producer": ("PDF producer", "PDF üreticisi"),
    "pages": ("Number of pages", "Sayfa sayısı"),
    "page_size": ("Page size", "Sayfa boyutu"),
    "location": ("Location", "Konum"),
    "file_size": ("File size", "Dosya boyutu"),
    # Settings
    "settings": ("Settings", "Ayarlar"),
    "app_theme": ("App theme", "Uygulama teması"),
    "theme_light": ("Light", "Açık"),
    "theme_dark": ("Dark", "Koyu"),
    "theme_system": ("Use system setting", "Sistem ayarını kullan"),
    "about": ("About", "Hakkında"),
    "about_text": ("PDF Reader for VeltOS. Version {version}. Pages are drawn by PDFium (Qt PDF).",
                   "VeltOS için PDF Okuyucu. Sürüm {version}. Sayfaları PDFium (Qt PDF) çizer."),
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
