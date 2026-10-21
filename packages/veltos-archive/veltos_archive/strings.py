"""Texts of VeltOS Archive (English, Turkish), in WinRAR's and Windows 11's
wording."""

import os

TEXTS = {
    "app_title": ("Archive", "Arşiv"),
    "menu_file": ("File", "Dosya"),
    "menu_commands": ("Commands", "Komutlar"),
    "menu_options": ("Options", "Seçenekler"),
    "menu_help": ("Help", "Yardım"),
    "open_archive": ("Open archive…", "Arşiv aç…"),
    "new_archive": ("New archive…", "Yeni arşiv…"),
    "exit": ("Exit", "Çıkış"),
    "add": ("Add", "Ekle"),
    "extract_to": ("Extract To", "Şuraya Çıkar"),
    "test": ("Test", "Sına"),
    "view": ("View", "Görüntüle"),
    "delete": ("Delete", "Sil"),
    "find": ("Find", "Bul"),
    "info": ("Info", "Bilgi"),
    "up": ("Up one level", "Bir üst düzey"),
    "about": ("About Archive", "Arşiv Hakkında"),
    "about_text": ("VeltOS Archive opens ZIP, RAR, 7Z, TAR, GZ, ISO and other archives and creates "
                   "ZIP, 7Z and TAR archives. It uses 7-Zip and libarchive. Creating RAR archives "
                   "needs RARLAB's own rar program.",
                   "VeltOS Arşiv ZIP, RAR, 7Z, TAR, GZ, ISO ve diğer arşivleri açar; ZIP, 7Z ve TAR "
                   "arşivleri oluşturur. 7-Zip ve libarchive kullanır. RAR arşivi oluşturmak için "
                   "RARLAB'ın kendi rar programı gerekir."),
    "col_name": ("Name", "Ad"),
    "col_size": ("Size", "Boyut"),
    "col_packed": ("Packed", "Sıkıştırılmış"),
    "col_type": ("Type", "Tür"),
    "col_modified": ("Modified", "Değiştirilme"),
    "col_crc": ("CRC32", "CRC32"),
    "folder_type": ("File folder", "Dosya klasörü"),
    "file_type": ("{ext} File", "{ext} Dosyası"),
    "file_type_plain": ("File", "Dosya"),
    "header": ("{name} - {type} archive, unpacked size {size} bytes",
               "{name} - {type} arşivi, açılmış boyut {size} bayt"),
    "total": ("Total {folders} folders and {files} files, {size} bytes",
              "Toplam {folders} klasör ve {files} dosya, {size} bayt"),
    "total_files": ("Total {files} files, {size} bytes", "Toplam {files} dosya, {size} bayt"),
    "selected": ("Selected {count} items, {size} bytes", "Seçili {count} öğe, {size} bayt"),
    "selected_one": ("Selected 1 item, {size} bytes", "Seçili 1 öğe, {size} bayt"),
    "empty_title": ("Open an archive", "Bir arşiv açın"),
    "empty_body": ("Open a ZIP, RAR, 7Z or other archive to see what is inside, or drop files here to "
                   "make a new archive.",
                   "İçinde ne olduğunu görmek için bir ZIP, RAR, 7Z veya başka bir arşiv açın ya da yeni "
                   "bir arşiv yapmak için dosyaları buraya bırakın."),
    "opening": ("Opening {name}…", "{name} açılıyor…"),
    "extract_title": ("Extraction path and options", "Çıkarma yolu ve seçenekleri"),
    "destination": ("Destination path (will be created if it does not exist)",
                    "Hedef yol (yoksa oluşturulur)"),
    "browse": ("Browse…", "Gözat…"),
    "overwrite_mode": ("Overwrite mode", "Üzerine yazma kipi"),
    "overwrite_rename": ("Rename automatically", "Otomatik yeniden adlandır"),
    "overwrite_all": ("Overwrite existing files", "Var olan dosyaların üzerine yaz"),
    "overwrite_skip": ("Skip existing files", "Var olan dosyaları atla"),
    "ok": ("OK", "Tamam"),
    "cancel": ("Cancel", "İptal"),
    "close": ("Close", "Kapat"),
    "add_title": ("Archive name and parameters", "Arşiv adı ve parametreleri"),
    "archive_name": ("Archive name", "Arşiv adı"),
    "archive_format": ("Archive format", "Arşiv biçimi"),
    "compression": ("Compression method", "Sıkıştırma yöntemi"),
    "level_store": ("Store", "Depola"),
    "level_fastest": ("Fastest", "En hızlı"),
    "level_fast": ("Fast", "Hızlı"),
    "level_normal": ("Normal", "Normal"),
    "level_good": ("Good", "İyi"),
    "level_best": ("Best", "En iyi"),
    "set_password": ("Set password…", "Parola belirle…"),
    "password_title": ("Enter password", "Parola girin"),
    "password_for": ("Enter password for {name}", "{name} için parolayı girin"),
    "password_new": ("Enter a password to protect the archive", "Arşivi korumak için bir parola girin"),
    "password": ("Password", "Parola"),
    "password_again": ("Reenter password (for verification)", "Parolayı yeniden girin (doğrulama için)"),
    "show_password": ("Show password", "Parolayı göster"),
    "encrypt_names": ("Encrypt file names", "Dosya adlarını şifrele"),
    "password_mismatch": ("The passwords do not match.", "Parolalar eşleşmiyor."),
    "wrong_password": ("The password is incorrect.", "Parola yanlış."),
    "rar_note": ("RAR archives can be opened and extracted; creating them needs WinRAR's own program.",
                 "RAR arşivleri açılabilir ve çıkarılabilir; oluşturmak için WinRAR'ın kendi programı gerekir."),
    "extracting": ("Extracting from {name}", "{name} dosyasından çıkarılıyor"),
    "adding": ("Creating archive {name}", "{name} arşivi oluşturuluyor"),
    "testing": ("Testing {name}", "{name} sınanıyor"),
    "deleting": ("Deleting from {name}", "{name} içinden siliniyor"),
    "elapsed": ("Elapsed time {time}", "Geçen süre {time}"),
    "background": ("Background", "Arka plan"),
    "test_ok": ("No errors found in {name}.", "{name} içinde hata bulunamadı."),
    "done_extract": ("Extracted to {folder}", "{folder} klasörüne çıkarıldı"),
    "show_files": ("Show files", "Dosyaları göster"),
    "failed": ("The operation did not complete.", "İşlem tamamlanamadı."),
    "unsupported": ("{name} is not an archive or is damaged.", "{name} bir arşiv değil ya da bozuk."),
    "confirm_delete": ("Delete {count} items from the archive?", "{count} öğe arşivden silinsin mi?"),
    "confirm_delete_body": ("This cannot be undone.", "Bu işlem geri alınamaz."),
    "info_title": ("Archive information", "Arşiv bilgisi"),
    "info_type": ("Archive type", "Arşiv türü"),
    "info_files": ("Files", "Dosyalar"),
    "info_folders": ("Folders", "Klasörler"),
    "info_size": ("Total size", "Toplam boyut"),
    "info_packed": ("Packed size", "Sıkıştırılmış boyut"),
    "info_ratio": ("Ratio", "Oran"),
    "info_solid": ("Solid", "Katı"),
    "info_locked": ("Password", "Parola"),
    "yes": ("Yes", "Evet"),
    "no": ("No", "Hayır"),
    "find_placeholder": ("Find in archive", "Arşivde bul"),
    "no_results": ("No files match “{query}”.", "“{query}” ile eşleşen dosya yok."),
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
