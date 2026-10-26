"""Texts of VeltOS Disk Management (English, Turkish), in the words of
Windows 11's Disk Management."""

import os

TEXTS = {
    "app_title": ("Disk Management", "Disk Yönetimi"),
    "refresh": ("Refresh", "Yenile"),
    "rescan": ("Rescan Disks", "Diskleri Yeniden Tara"),
    "working": ("Working…", "Çalışıyor…"),
    "no_disks": ("No disks were found.", "Disk bulunamadı."),
    "udisks_error": ("The disk service (UDisks2) could not be read: {error}",
                     "Disk hizmeti (UDisks2) okunamadı: {error}"),
    # Volume list columns
    "volume": ("Volume", "Birim"),
    "layout": ("Layout", "Düzen"),
    "type": ("Type", "Tür"),
    "file_system": ("File System", "Dosya Sistemi"),
    "status": ("Status", "Durum"),
    "capacity": ("Capacity", "Kapasite"),
    "free_space": ("Free Space", "Boş Alan"),
    "percent_free": ("% Free", "% Boş"),
    "simple": ("Simple", "Basit"),
    "basic": ("Basic", "Temel"),
    "healthy": ("Healthy", "İyi durumda"),
    "healthy_with": ("Healthy ({parts})", "İyi durumda ({parts})"),
    "part_system": ("System", "Sistem"),
    "part_boot": ("Boot", "Önyükleme"),
    "part_efi": ("EFI System Partition", "EFI Sistem Bölümü"),
    "part_recovery": ("Recovery Partition", "Kurtarma Bölümü"),
    "part_reserved": ("Reserved Partition", "Ayrılmış Bölüm"),
    "part_bios": ("BIOS Boot Partition", "BIOS Önyükleme Bölümü"),
    "part_swap": ("Swap", "Takas"),
    "part_primary": ("Primary Partition", "Birincil Bölüm"),
    "part_data": ("Basic Data Partition", "Temel Veri Bölümü"),
    "part_logical": ("Logical Drive", "Mantıksal Sürücü"),
    "part_optical": ("Optical Disc", "Optik Disk"),
    "part_readonly": ("Read-only", "Salt okunur"),
    "local_disk": ("Local Disk", "Yerel Disk"),
    "partition_of": ("(Disk {disk} partition {number})", "(Disk {disk} bölüm {number})"),
    "raw": ("RAW", "RAW"),
    # Disk map
    "disk_n": ("Disk {number}", "Disk {number}"),
    "cdrom_n": ("CD-ROM {number}", "CD-ROM {number}"),
    "removable": ("Removable", "Çıkarılabilir"),
    "dvd": ("DVD", "DVD"),
    "online": ("Online", "Çevrimiçi"),
    "no_media": ("No Media", "Ortam Yok"),
    "not_initialized": ("Not Initialized", "Başlatılmamış"),
    "read_only": ("Read Only", "Salt Okunur"),
    "unallocated": ("Unallocated", "Ayrılmamış"),
    "free": ("Free space", "Boş alan"),
    "unknown": ("Unknown", "Bilinmiyor"),
    # Menu
    "open": ("Open", "Aç"),
    "explore": ("Explore", "Gözat"),
    "mount": ("Mount", "Bağla"),
    "unmount": ("Unmount", "Bağlantıyı kes"),
    "eject": ("Eject", "Çıkar"),
    "change_label": ("Change Volume Label…", "Birim Etiketini Değiştir…"),
    "format": ("Format…", "Biçimlendir…"),
    "delete_volume": ("Delete Volume…", "Birimi Sil…"),
    "new_volume": ("New Simple Volume…", "Yeni Basit Birim…"),
    "initialize": ("Initialize Disk…", "Diski Başlat…"),
    "properties": ("Properties", "Özellikler"),
    # Dialogs
    "ok": ("OK", "Tamam"),
    "cancel": ("Cancel", "İptal"),
    "yes": ("Yes", "Evet"),
    "no": ("No", "Hayır"),
    "format_title": ("Format {name}", "{name} birimini biçimlendir"),
    "volume_label": ("Volume label", "Birim etiketi"),
    "fs_choice": ("File system", "Dosya sistemi"),
    "quick_format": ("Perform a quick format", "Hızlı biçimlendirme yap"),
    "format_warning": ("Formatting this volume will erase all data on it. Back up any data you want to keep "
                       "before formatting. Do you want to continue?",
                       "Bu birimi biçimlendirmek üzerindeki tüm verileri siler. Biçimlendirmeden önce saklamak "
                       "istediğiniz verileri yedekleyin. Devam etmek istiyor musunuz?"),
    "format_unavailable": ("This volume is in use by the running system, is read-only, or is no longer available.",
                           "Bu birim çalışan sistem tarafından kullanılıyor, salt okunur veya artık kullanılamıyor."),
    "delete_title": ("Delete simple volume", "Basit birimi sil"),
    "delete_warning": ("Deleting this volume will erase all data on it. Back up any data you want to keep "
                       "before deleting. Do you want to continue?",
                       "Bu birimi silmek üzerindeki tüm verileri siler. Silmeden önce saklamak istediğiniz "
                       "verileri yedekleyin. Devam etmek istiyor musunuz?"),
    "new_volume_title": ("New Simple Volume", "Yeni Basit Birim"),
    "volume_size": ("Simple volume size in MB", "Basit birim boyutu (MB)"),
    "max_size": ("Maximum disk space in MB: {size}", "En fazla disk alanı (MB): {size}"),
    "label_title": ("Change volume label", "Birim etiketini değiştir"),
    "initialize_title": ("Initialize Disk", "Diski Başlat"),
    "initialize_text": ("You must initialize a disk before it can be used. Choose the partition style for "
                        "{name}. GPT is right for every PC made after 2010; MBR is for old PCs.",
                        "Bir disk kullanılmadan önce başlatılmalıdır. {name} için bölüm stilini seçin. "
                        "GPT, 2010'dan sonra üretilen her PC için uygundur; MBR eski PC'ler içindir."),
    "style": ("Partition style", "Bölüm stili"),
    "gpt": ("GPT (GUID Partition Table)", "GPT (GUID Bölüm Tablosu)"),
    "mbr": ("MBR (Master Boot Record)", "MBR (Ana Önyükleme Kaydı)"),
    "properties_title": ("{name} Properties", "{name} Özellikleri"),
    "prop_device": ("Device", "Aygıt"),
    "prop_mount": ("Mount point", "Bağlama noktası"),
    "prop_used": ("Used space", "Kullanılan alan"),
    "prop_uuid": ("UUID", "UUID"),
    "prop_disk": ("Disk", "Disk"),
    "prop_model": ("Model", "Model"),
    "not_mounted": ("Not mounted", "Bağlı değil"),
    "failed": ("The operation did not complete: {error}", "İşlem tamamlanamadı: {error}"),
    "system_volume": ("This volume is in use by the running system and cannot be changed.",
                      "Bu birim çalışan sistem tarafından kullanılıyor ve değiştirilemez."),
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
