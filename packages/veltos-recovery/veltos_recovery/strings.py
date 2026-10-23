"""Texts of VeltOS' automatic repair, in English and Turkish."""

TEXTS = {
    "title": ("VeltOS couldn't start correctly", "VeltOS düzgün başlatılamadı"),
    "body": ("VeltOS tried to start twice and could not finish. Restarting can fix the problem. "
             "You can also open Advanced options to repair your PC.",
             "VeltOS iki kez başlatılmaya çalışıldı ve tamamlanamadı. Yeniden başlatmak sorunu "
             "çözebilir. Bilgisayarınızı onarmak için Gelişmiş seçenekleri de açabilirsiniz."),
    "manual_title": ("Automatic Repair", "Otomatik Onarım"),
    "manual_body": ("Choose how to repair VeltOS or how to continue.",
                    "VeltOS'u nasıl onaracağınızı veya nasıl devam edeceğinizi seçin."),
    "advanced": ("Advanced options", "Gelişmiş seçenekler"),
    "restart": ("Restart", "Yeniden başlat"),
    "choose": ("Choose an option", "Bir seçenek belirleyin"),
    "back": ("Back", "Geri"),
    "repair": ("Startup Repair", "Başlangıç Onarımı"),
    "repair_desc": ("Fix problems that keep VeltOS from starting",
                    "VeltOS'un başlamasını engelleyen sorunları düzeltin"),
    "safe": ("Safe mode", "Güvenli mod"),
    "safe_desc": ("Start VeltOS once with basic graphics", "VeltOS'u bir kez temel grafiklerle başlatın"),
    "terminal": ("Command Prompt", "Komut İstemi"),
    "terminal_desc": ("Use a terminal for advanced repair; sign in with your account",
                      "Gelişmiş onarım için terminali kullanın; hesabınızla oturum açın"),
    "details": ("Problem details", "Sorun ayrıntıları"),
    "details_desc": ("See what went wrong while VeltOS was starting",
                     "VeltOS başlatılırken neyin yanlış gittiğini görün"),
    "continue": ("Continue", "Devam et"),
    "continue_desc": ("Exit and start VeltOS normally", "Çıkın ve VeltOS'u normal şekilde başlatın"),
    "off": ("Turn off your PC", "Bilgisayarınızı kapatın"),
    "off_desc": ("Shut down the PC", "Bilgisayarı kapatın"),
    "repairing": ("Repairing your PC", "Bilgisayarınız onarılıyor"),
    "repairing_body": ("This can take a few minutes. Don't turn off your PC.",
                       "Bu işlem birkaç dakika sürebilir. Bilgisayarınızı kapatmayın."),
    "repair_done": ("Startup Repair finished", "Başlangıç Onarımı tamamlandı"),
    "repair_done_body": ("Restart to start VeltOS. If it still doesn't start, open Advanced options again.",
                         "VeltOS'u başlatmak için yeniden başlatın. Hâlâ başlamazsa Gelişmiş seçenekleri yeniden açın."),
    "repair_failed": ("Startup Repair couldn't fix everything", "Başlangıç Onarımı her şeyi düzeltemedi"),
    "repair_failed_body": ("The output below shows what went wrong. You can still try to restart, "
                           "use Safe mode or the Command Prompt.",
                           "Aşağıdaki çıktı neyin yanlış gittiğini gösteriyor. Yine de yeniden "
                           "başlatmayı, Güvenli modu veya Komut İstemini deneyebilirsiniz."),
    "step_packages": ("Finishing interrupted updates", "Yarım kalan güncelleştirmeler tamamlanıyor"),
    "step_dependencies": ("Repairing installed apps", "Yüklü uygulamalar onarılıyor"),
    "step_space": ("Making room on the disk", "Diskte yer açılıyor"),
    "step_initramfs": ("Rebuilding the start-up files", "Başlangıç dosyaları yeniden oluşturuluyor"),
    "step_grub": ("Rebuilding the boot menu", "Önyükleme menüsü yeniden oluşturuluyor"),
    "step_services": ("Resetting system services", "Sistem hizmetleri sıfırlanıyor"),
    "space_ok": ("There is enough free space.", "Yeterli boş alan var."),
    "space_freed": ("Freed space: removed downloaded packages and old logs.",
                    "Yer açıldı: indirilmiş paketler ve eski günlükler kaldırıldı."),
    "details_title": ("Problem details", "Sorun ayrıntıları"),
    "details_body": ("Errors VeltOS recorded while it was starting the last time.",
                     "VeltOS'un son başlatılışında kaydettiği hatalar."),
    "details_none": ("No record of the last start was kept (the PC may have stopped before it could "
                     "write one).",
                     "Son başlatılışın kaydı tutulamadı (bilgisayar kayıt yazamadan durmuş olabilir)."),
    "terminal_open": ("The terminal is open on a text screen. Type exit there to come back here.",
                      "Terminal bir metin ekranında açık. Buraya dönmek için orada exit yazın."),
    # Above the text console's sign-in prompt (Command Prompt).
    "terminal_hint": ("VeltOS Automatic Repair - Command Prompt. Sign in with your account. "
                      "Type exit to go back to Automatic Repair.",
                      "VeltOS Otomatik Onarım - Komut İstemi. Hesabınızla oturum açın. "
                      "Otomatik Onarım'a dönmek için exit yazın."),
    "working": ("Please wait…", "Lütfen bekleyin…"),
}


def text(lang, key):
    english, turkish = TEXTS[key]
    return turkish if lang == "tr" else english
