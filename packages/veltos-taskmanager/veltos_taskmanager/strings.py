"""Texts of VeltOS Task Manager (English, Turkish), in Windows 11 wording."""

import os

TEXTS = {
    "app_title": ("Task Manager", "Görev Yöneticisi"),
    "processes": ("Processes", "İşlemler"),
    "performance": ("Performance", "Performans"),
    "startup": ("Startup apps", "Başlangıç uygulamaları"),
    "apps": ("Apps", "Uygulamalar"),
    "background": ("Background processes", "Arka plan işlemleri"),
    "system": ("System processes", "Sistem işlemleri"),
    "name": ("Name", "Ad"),
    "cpu": ("CPU", "CPU"),
    "memory": ("Memory", "Bellek"),
    "disk": ("Disk", "Disk"),
    "network": ("Network", "Ağ"),
    "status": ("Status", "Durum"),
    "end_task": ("End task", "Görevi sonlandır"),
    "run_task": ("Run new task", "Yeni görev çalıştır"),
    "search": ("Type a name to search", "Aramak için bir ad yazın"),
    "enabled": ("Enabled", "Etkin"),
    "disabled": ("Disabled", "Devre dışı"),
    "enable": ("Enable", "Etkinleştir"),
    "disable": ("Disable", "Devre dışı bırak"),
    "utilization": ("Utilization", "Kullanım"),
    "speed": ("Speed", "Hız"),
    "processes_count": ("Processes", "İşlemler"),
    "uptime": ("Up time", "Çalışma süresi"),
    "cores": ("Cores", "Çekirdekler"),
    "logical": ("Logical processors", "Mantıksal işlemciler"),
    "in_use": ("In use", "Kullanımda"),
    "available": ("Available", "Kullanılabilir"),
    "total": ("Total", "Toplam"),
    "read": ("Read speed", "Okuma hızı"),
    "write": ("Write speed", "Yazma hızı"),
    "send": ("Send", "Gönder"),
    "receive": ("Receive", "Al"),
    "over_60": ("% utilization over 60 seconds", "60 saniyedeki kullanım yüzdesi"),
    "no_startup": ("No startup apps.", "Başlangıç uygulaması yok."),
    "startup_note": ("Apps that start when you sign in.", "Oturum açtığınızda başlayan uygulamalar."),
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
