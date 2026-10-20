"""User interface texts of VeltOS File Explorer (English and Turkish), in
the words Windows 11 File Explorer uses."""

import os

TEXTS = {
    "app_title": ("File Explorer", "Dosya Gezgini"),
    "home": ("Home", "Giriş"),
    "this_pc": ("This PC", "Bu bilgisayar"),
    "recycle_bin": ("Recycle Bin", "Geri Dönüşüm Kutusu"),
    "quick_access": ("Quick access", "Hızlı erişim"),
    "recent": ("Recent", "Son kullanılanlar"),
    "no_recent": ("After you've opened some files, we'll show the most recent ones here.",
                  "Bazı dosyaları açtıktan sonra en son kullanılanları burada göstereceğiz."),
    "stored_locally": ("Stored locally", "Yerel olarak depolanıyor"),
    "devices_and_drives": ("Devices and drives", "Cihazlar ve sürücüler"),
    "local_disk": ("Local Disk", "Yerel Disk"),
    "windows_read_only": ("This Windows drive is open read-only: Windows did not shut down completely "
                          "(Fast Startup or hibernation), and writing to it now could damage it. To change "
                          "files, start Windows and choose Shut down while holding Shift.",
                          "Bu Windows sürücüsü salt okunur açıldı: Windows tamamen kapanmamış (Hızlı Başlatma "
                          "veya hazırda bekletme) ve şimdi yazmak sürücüye zarar verebilir. Dosyaları "
                          "değiştirmek için Windows'u başlatıp Shift'e basılıyken Kapat'ı seçin."),
    "usb_drive": ("USB Drive", "USB Sürücü"),
    "free_of": ("{free} free of {total}", "{total} alanın {free} kadarı boş"),
    "not_mounted": ("Double-click to open", "Açmak için çift tıklayın"),
    "new_tab": ("New tab", "Yeni sekme"),
    "close_tab": ("Close tab", "Sekmeyi kapat"),
    "minimize": ("Minimize", "Simge durumuna küçült"),
    "maximize": ("Maximize", "Ekranı kapla"),
    "restore_down": ("Restore Down", "Önceki boyut"),
    "close": ("Close", "Kapat"),
    # Command bar
    "new": ("New", "Yeni"),
    "folder": ("Folder", "Klasör"),
    "text_document": ("Text Document", "Metin Belgesi"),
    "new_folder_name": ("New folder", "Yeni klasör"),
    "new_text_name": ("New Text Document.txt", "Yeni Metin Belgesi.txt"),
    "cut": ("Cut", "Kes"),
    "copy": ("Copy", "Kopyala"),
    "paste": ("Paste", "Yapıştır"),
    "rename": ("Rename", "Yeniden adlandır"),
    "delete": ("Delete", "Sil"),
    "sort": ("Sort", "Sırala"),
    "view": ("View", "Görünüm"),
    "see_more": ("See more", "Daha fazlasını gör"),
    "name": ("Name", "Ad"),
    "date_modified": ("Date modified", "Değiştirme tarihi"),
    "type": ("Type", "Tür"),
    "size": ("Size", "Boyut"),
    "ascending": ("Ascending", "Artan"),
    "descending": ("Descending", "Azalan"),
    "extra_large_icons": ("Extra large icons", "Çok büyük simgeler"),
    "large_icons": ("Large icons", "Büyük simgeler"),
    "medium_icons": ("Medium icons", "Orta boyutlu simgeler"),
    "small_icons": ("Small icons", "Küçük simgeler"),
    "details": ("Details", "Ayrıntılar"),
    "tiles": ("Tiles", "Döşemeler"),
    "show": ("Show", "Göster"),
    "hidden_items": ("Hidden items", "Gizli öğeler"),
    "select_all": ("Select all", "Tümünü seç"),
    "select_none": ("Select none", "Hiçbirini seçme"),
    "invert_selection": ("Invert selection", "Seçimi tersine çevir"),
    "properties": ("Properties", "Özellikler"),
    "open_in_terminal": ("Open in Terminal", "Terminalde aç"),
    "empty_recycle_bin": ("Empty Recycle Bin", "Geri Dönüşüm Kutusunu boşalt"),
    "restore": ("Restore", "Geri yükle"),
    "restore_all": ("Restore all items", "Tüm öğeleri geri yükle"),
    # Address and search
    "back": ("Back", "Geri"),
    "forward": ("Forward", "İleri"),
    "up": ("Up to \"{name}\"", "\"{name}\" konumuna yukarı"),
    "refresh": ("Refresh", "Yenile"),
    "search_in": ("Search {name}", "{name} içinde ara"),
    "search_results": ("Search results in {name}", "{name} içindeki arama sonuçları"),
    "searching": ("Searching…", "Aranıyor…"),
    "no_results": ("No items match your search.", "Aramanızla eşleşen öğe yok."),
    "folder_empty": ("This folder is empty.", "Bu klasör boş."),
    "location": ("Location", "Konum"),
    "original_location": ("Original location", "Özgün konum"),
    "date_deleted": ("Date deleted", "Silinme tarihi"),
    # Context menu
    "open": ("Open", "Aç"),
    "open_in_new_tab": ("Open in new tab", "Yeni sekmede aç"),
    "open_with": ("Open with", "Birlikte aç"),
    "choose_another_app": ("Choose another app", "Başka bir uygulama seç"),
    "pin_to_quick_access": ("Pin to Quick access", "Hızlı erişime sabitle"),
    "unpin_from_quick_access": ("Unpin from Quick access", "Hızlı erişimden kaldır"),
    "compress_zip": ("Compress to ZIP file", "ZIP dosyasına sıkıştır"),
    "extract_all": ("Extract All…", "Tümünü Ayıkla…"),
    "copy_as_path": ("Copy as path", "Yol olarak kopyala"),
    "eject": ("Eject", "Çıkar"),
    # Status bar
    "items": ("{count} items", "{count} öğe"),
    "item": ("1 item", "1 öğe"),
    "selected": ("{count} items selected", "{count} öğe seçili"),
    "one_selected": ("1 item selected", "1 öğe seçili"),
    # Messages
    "file_folder": ("File folder", "Dosya klasörü"),
    "file": ("File", "Dosya"),
    "delete_title": ("Delete multiple items", "Birden çok öğeyi sil"),
    "delete_forever": ("Are you sure you want to permanently delete these {count} items?",
                       "Bu {count} öğeyi kalıcı olarak silmek istediğinizden emin misiniz?"),
    "delete_forever_one": ("Are you sure you want to permanently delete \"{name}\"?",
                           "\"{name}\" öğesini kalıcı olarak silmek istediğinizden emin misiniz?"),
    "empty_bin_question": ("Are you sure you want to permanently delete all items in the Recycle Bin?",
                           "Geri Dönüşüm Kutusundaki tüm öğeleri kalıcı olarak silmek istediğinizden emin misiniz?"),
    "yes": ("Yes", "Evet"),
    "no": ("No", "Hayır"),
    "ok": ("OK", "Tamam"),
    "cannot_open": ("VeltOS can't find \"{name}\". Check the spelling and try again.",
                    "\"{name}\" bulunamıyor. Yazımı denetleyip yeniden deneyin."),
    "no_access": ("You don't currently have permission to access this folder.",
                  "Şu anda bu klasöre erişim izniniz yok."),
    "rename_exists": ("There is already a file with the same name in this location.",
                      "Bu konumda aynı ada sahip bir dosya zaten var."),
    "rename_invalid": ("A file name can't contain the / character.", "Dosya adı / karakterini içeremez."),
    "rename_empty": ("You must type a file name.", "Bir dosya adı yazmanız gerekiyor."),
    "restore_exists": ("An item with this name is already in the original location.",
                       "Özgün konumda bu ada sahip bir öğe zaten var."),
}


def language(environ=None):
    environ = os.environ if environ is None else environ
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = environ.get(variable)
        if value:
            return "tr" if value.lower().startswith("tr") else "en"
    return "en"


def text(lang, key, **values):
    pair = TEXTS[key]
    result = pair[1] if lang == "tr" else pair[0]
    return result.format(**values) if values else result
