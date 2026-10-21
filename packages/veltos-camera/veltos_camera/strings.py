"""Texts of VeltOS Camera (English, Turkish), in Windows 11 wording."""

import os

TEXTS = {
    "app_title": ("Camera", "Kamera"),
    "photo": ("Photo", "Fotoğraf"),
    "video": ("Video", "Video"),
    "take_photo": ("Take photo", "Fotoğraf çek"),
    "start_video": ("Take video", "Video çek"),
    "stop_video": ("Stop taking video", "Video çekmeyi durdur"),
    "change_camera": ("Change camera", "Kamerayı değiştir"),
    "settings": ("Settings", "Ayarlar"),
    "close": ("Close", "Kapat"),
    "timer": ("Photo timer", "Fotoğraf zamanlayıcısı"),
    "timer_off": ("Off", "Kapalı"),
    "seconds": ("{n} s", "{n} sn"),
    "no_camera_title": ("We can't find your camera", "Kameranızı bulamıyoruz"),
    "no_camera_body": ("Check that it's connected properly and that no other app is using it.",
                       "Doğru bağlandığından ve başka bir uygulamanın kullanmadığından emin olun."),
    "camera_error": ("Something went wrong with the camera", "Kamerada bir sorun oluştu"),
    "camera_settings": ("Camera settings", "Kamera ayarları"),
    "framing_grid": ("Framing grid", "Çerçeve kılavuzu"),
    "grid_none": ("None", "Yok"),
    "grid_thirds": ("Rule of thirds", "Üçler kuralı"),
    "grid_square": ("Square", "Kare"),
    "grid_cross": ("Crosshairs", "Artı işareti"),
    "video_settings": ("Video settings", "Video ayarları"),
    "record_audio": ("Record audio with videos", "Videolarla birlikte ses kaydet"),
    "save_location": ("Save location", "Kayıt konumu"),
    "save_location_body": ("Photos and videos are saved in {folder}",
                           "Fotoğraflar ve videolar şuraya kaydedilir: {folder}"),
    "open_folder": ("Open folder", "Klasörü aç"),
    "last_capture": ("Open the last photo or video", "Son fotoğrafı veya videoyu aç"),
    "save_failed": ("The photo or video could not be saved.", "Fotoğraf veya video kaydedilemedi."),
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
