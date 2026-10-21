"""Texts of VeltOS Photos in English and Turkish (Windows 11 Photos'
wording)."""

import os

TEXTS = {
    "app_title": ("Photos", "Fotoğraflar"),
    "search": ("Search", "Ara"),
    "gallery": ("Gallery", "Galeri"),
    "favorites": ("Favorites", "Sık Kullanılanlar"),
    "folders": ("Folders", "Klasörler"),
    "add_folder": ("Add a folder", "Klasör ekle"),
    "remove_folder": ("Remove folder", "Klasörü kaldır"),
    "settings": ("Settings", "Ayarlar"),
    "minimize": ("Minimize", "Simge durumuna küçült"),
    "maximize": ("Maximize", "Ekranı kapla"),
    "restore_down": ("Restore down", "Önceki boyut"),
    "close": ("Close", "Kapat"),
    "back": ("Back", "Geri"),
    # Gallery toolbar
    "filter": ("Filter", "Filtre"),
    "all_items": ("Photos and videos", "Fotoğraflar ve videolar"),
    "photos_only": ("Photos", "Fotoğraflar"),
    "videos_only": ("Videos", "Videolar"),
    "sort": ("Sort", "Sırala"),
    "newest": ("Date taken: newest first", "Çekim tarihi: önce en yeni"),
    "oldest": ("Date taken: oldest first", "Çekim tarihi: önce en eski"),
    "view": ("View", "Görünüm"),
    "small": ("Small", "Küçük"),
    "medium": ("Medium", "Orta"),
    "large": ("Large", "Büyük"),
    "slideshow": ("Slideshow", "Slayt gösterisi"),
    "items": ("{count} items", "{count} öğe"),
    "one_item": ("1 item", "1 öğe"),
    "scanning": ("Looking for photos and videos…", "Fotoğraflar ve videolar aranıyor…"),
    "empty_title": ("Your photos and videos will show here", "Fotoğraflarınız ve videolarınız burada görünür"),
    "empty_text": ("Put pictures in your Pictures folder, or add a folder in the folder list.",
                   "Resimlerinizi Resimler klasörüne koyun veya klasör listesinden bir klasör ekleyin."),
    "no_favorites": ("Select the heart on a photo to add it to your favorites.",
                     "Sık kullanılanlarınıza eklemek için bir fotoğraftaki kalbi seçin."),
    "no_results": ("No photos or videos match “{text}”.",
                   "“{text}” ile eşleşen fotoğraf veya video yok."),
    # Viewer
    "zoom_in": ("Zoom in", "Yakınlaştır"),
    "zoom_out": ("Zoom out", "Uzaklaştır"),
    "fit": ("Fit to window", "Pencereye sığdır"),
    "actual_size": ("View actual size", "Gerçek boyutta görüntüle"),
    "rotate": ("Rotate", "Döndür"),
    "edit": ("Edit image", "Görüntüyü düzenle"),
    "delete": ("Delete", "Sil"),
    "favorite": ("Add to favorites", "Sık kullanılanlara ekle"),
    "unfavorite": ("Remove from favorites", "Sık kullanılanlardan kaldır"),
    "file_info": ("File information", "Dosya bilgileri"),
    "more": ("See more", "Daha fazlasını görün"),
    "previous": ("Previous", "Önceki"),
    "next": ("Next", "Sonraki"),
    "copy": ("Copy", "Kopyala"),
    "set_as": ("Set as", "Farklı ayarla"),
    "set_background": ("Set as background", "Arka plan olarak ayarla"),
    "set_lock_screen": ("Set as lock screen", "Kilit ekranı olarak ayarla"),
    "open_with": ("Open with", "Birlikte aç"),
    "show_in_folder": ("Show in folder", "Klasörde göster"),
    "play_video": ("Play in Media Player", "Medya Oynatıcı'da oynat"),
    "delete_title": ("Delete this file?", "Bu dosya silinsin mi?"),
    "delete_text": ("“{name}” will move to the Recycle Bin.",
                    "“{name}” Geri Dönüşüm Kutusu'na taşınacak."),
    "cancel": ("Cancel", "İptal"),
    "ok": ("OK", "Tamam"),
    "cant_open": ("Photos can't open this file.", "Fotoğraflar bu dosyayı açamıyor."),
    "cant_save": ("The picture could not be saved: {error}", "Resim kaydedilemedi: {error}"),
    "background_set": ("Desktop background changed.", "Masaüstü arka planı değiştirildi."),
    "lock_set": ("Lock screen picture changed.", "Kilit ekranı resmi değiştirildi."),
    "copied": ("Copied", "Kopyalandı"),
    # File information
    "date_taken": ("Date taken", "Çekim tarihi"),
    "date_modified": ("Date modified", "Değiştirilme tarihi"),
    "dimensions": ("Dimensions", "Boyutlar"),
    "file_size": ("File size", "Dosya boyutu"),
    "location": ("Location", "Konum"),
    "camera": ("Camera", "Kamera"),
    "lens": ("Lens", "Lens"),
    "exposure": ("Exposure", "Pozlama"),
    "file_name": ("File name", "Dosya adı"),
    # Edit
    "crop": ("Crop", "Kırp"),
    "adjust": ("Adjustment", "Ayarlama"),
    "aspect": ("Aspect ratio", "En boy oranı"),
    "aspect_free": ("Free", "Serbest"),
    "aspect_original": ("Original", "Özgün"),
    "aspect_square": ("Square", "Kare"),
    "rotate_left": ("Rotate left", "Sola döndür"),
    "rotate_right": ("Rotate right", "Sağa döndür"),
    "flip": ("Flip horizontal", "Yatay çevir"),
    "reset": ("Reset", "Sıfırla"),
    "brightness": ("Brightness", "Parlaklık"),
    "contrast": ("Contrast", "Karşıtlık"),
    "saturation": ("Saturation", "Doygunluk"),
    "warmth": ("Warmth", "Sıcaklık"),
    "save": ("Save", "Kaydet"),
    "save_copy": ("Save as copy", "Kopya olarak kaydet"),
    "copy_word": ("Copy", "Kopya"),
    "discard_title": ("Discard your changes?", "Değişiklikleriniz atılsın mı?"),
    "discard": ("Discard", "At"),
    # Settings
    "appearance": ("Appearance", "Görünüm"),
    "app_theme": ("App theme", "Uygulama teması"),
    "theme_light": ("Light", "Açık"),
    "theme_dark": ("Dark", "Koyu"),
    "theme_system": ("Use system setting", "Sistem ayarını kullan"),
    "folders_desc": ("Photos shows the pictures and videos of these folders and their subfolders.",
                     "Fotoğraflar bu klasörlerdeki ve alt klasörlerindeki resimleri ve videoları gösterir."),
    "about": ("About", "Hakkında"),
    "about_text": ("Photos for VeltOS, in the look of Windows 11 Photos. Version {version}.",
                   "VeltOS için Fotoğraflar, Windows 11 Fotoğraflar görünümünde. Sürüm {version}."),
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
