"""Texts of VeltOS Media Player in English and Turkish (Windows 11 Media
Player's wording)."""

import os

TEXTS = {
    "app_title": ("Media Player", "Medya Oynatıcı"),
    "search": ("Search", "Ara"),
    "home": ("Home", "Giriş"),
    "music_library": ("Music library", "Müzik kitaplığı"),
    "video_library": ("Video library", "Video kitaplığı"),
    "play_queue": ("Play queue", "Çalma kuyruğu"),
    "playlists": ("Playlists", "Çalma listeleri"),
    "settings": ("Settings", "Ayarlar"),
    "minimize": ("Minimize", "Simge durumuna küçült"),
    "maximize": ("Maximize", "Ekranı kapla"),
    "restore_down": ("Restore down", "Önceki boyut"),
    "close": ("Close", "Kapat"),
    "back": ("Back", "Geri"),
    # Home
    "recent_media": ("Recent media", "Son medya"),
    "no_recent": ("Media you play will show here.", "Oynattığınız medya burada görünür."),
    "open_files": ("Open file(s)", "Dosya(ları) aç"),
    "media_files": ("Media files", "Medya dosyaları"),
    # Music
    "music": ("Music", "Müzik"),
    "songs": ("Songs", "Şarkılar"),
    "albums": ("Albums", "Albümler"),
    "artists": ("Artists", "Sanatçılar"),
    "shuffle_and_play": ("Shuffle and play", "Karıştır ve çal"),
    "play_all": ("Play all", "Tümünü çal"),
    "title": ("Title", "Başlık"),
    "artist": ("Artist", "Sanatçı"),
    "album": ("Album", "Albüm"),
    "year": ("Year", "Yıl"),
    "genre": ("Genre", "Tür"),
    "length": ("Length", "Uzunluk"),
    "unknown_artist": ("Unknown artist", "Bilinmeyen sanatçı"),
    "unknown_album": ("Unknown album", "Bilinmeyen albüm"),
    "songs_count": ("{count} songs", "{count} şarkı"),
    "one_song": ("1 song", "1 şarkı"),
    "empty_music": ("Your music will show here. Put songs in your Music folder or add a folder in Settings.",
                    "Müziğiniz burada görünür. Şarkıları Müzik klasörüne koyun veya Ayarlar'dan klasör ekleyin."),
    # Video
    "videos": ("Videos", "Videolar"),
    "empty_videos": ("Your videos will show here. Put them in your Videos folder or add a folder in Settings.",
                     "Videolarınız burada görünür. Videoları Videolar klasörüne koyun veya Ayarlar'dan klasör ekleyin."),
    # Queue and playlists
    "clear": ("Clear", "Temizle"),
    "empty_queue": ("Songs and videos you play or add to the queue will show here.",
                    "Oynattığınız veya kuyruğa eklediğiniz şarkılar ve videolar burada görünür."),
    "new_playlist": ("New playlist", "Yeni çalma listesi"),
    "playlist_name": ("Name this playlist", "Bu çalma listesini adlandırın"),
    "untitled_playlist": ("Untitled playlist", "Adsız çalma listesi"),
    "create": ("Create", "Oluştur"),
    "cancel": ("Cancel", "İptal"),
    "delete_playlist": ("Delete playlist", "Çalma listesini sil"),
    "empty_playlists": ("Create a playlist and add songs to it from the music library.",
                        "Bir çalma listesi oluşturun ve müzik kitaplığından şarkı ekleyin."),
    "empty_playlist": ("Add songs to this playlist from the music library.",
                       "Müzik kitaplığından bu çalma listesine şarkı ekleyin."),
    # Item menus
    "play": ("Play", "Çal"),
    "play_next": ("Play next", "Sonra çal"),
    "add_to": ("Add to", "Şuraya ekle"),
    "remove": ("Remove", "Kaldır"),
    "show_in_folder": ("Show in folder", "Klasörde göster"),
    "properties": ("Properties", "Özellikler"),
    # Player
    "now_playing": ("Now playing", "Şimdi çalınıyor"),
    "pause": ("Pause", "Duraklat"),
    "previous": ("Previous", "Önceki"),
    "next": ("Next", "Sonraki"),
    "shuffle_on": ("Shuffle: On", "Karıştır: Açık"),
    "shuffle_off": ("Shuffle: Off", "Karıştır: Kapalı"),
    "repeat_off": ("Repeat: Off", "Yinele: Kapalı"),
    "repeat_all": ("Repeat: All", "Yinele: Tümü"),
    "repeat_one": ("Repeat: One", "Yinele: Bir"),
    "mute": ("Mute", "Sesi kapat"),
    "unmute": ("Unmute", "Sesi aç"),
    "volume": ("Volume", "Ses düzeyi"),
    "full_screen": ("Full screen", "Tam ekran"),
    "exit_full_screen": ("Exit full screen", "Tam ekrandan çık"),
    "speed": ("Speed", "Hız"),
    "normal_speed": ("Normal", "Normal"),
    "cant_play": ("Media Player can't play this file.", "Medya Oynatıcı bu dosyayı oynatamıyor."),
    "nothing_playing": ("Nothing is playing", "Hiçbir şey çalınmıyor"),
    # Settings
    "appearance": ("Appearance", "Görünüm"),
    "app_theme": ("App theme", "Uygulama teması"),
    "theme_light": ("Light", "Açık"),
    "theme_dark": ("Dark", "Koyu"),
    "theme_system": ("Use system setting", "Sistem ayarını kullan"),
    "library": ("Library", "Kitaplık"),
    "music_folders": ("Music library locations", "Müzik kitaplığı konumları"),
    "video_folders": ("Video library locations", "Video kitaplığı konumları"),
    "add_folder": ("Add folder", "Klasör ekle"),
    "remove_folder": ("Remove", "Kaldır"),
    "refresh": ("Refresh libraries", "Kitaplıkları yenile"),
    "about": ("About", "Hakkında"),
    "about_text": ("Media Player for VeltOS, in the look of Windows 11 Media Player. Version {version}.",
                   "VeltOS için Medya Oynatıcı, Windows 11 Medya Oynatıcı görünümünde. Sürüm {version}."),
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
