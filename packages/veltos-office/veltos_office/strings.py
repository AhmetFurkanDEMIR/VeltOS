"""Texts of the VeltOS Office start pages (English and Turkish), in the
words of Microsoft 365's Home / New / Open pages on Windows 11."""

import os

# kind -> (app title, Turkish), blank document tile, Turkish
KINDS = {
    "word": ("Word Processor", "Kelime İşlemci"),
    "sheet": ("Spreadsheet", "Hesap Tablosu"),
    "slides": ("Presentation", "Sunu"),
}

TEXTS = {
    "office": ("VeltOS Office", "VeltOS Office"),
    # Navigation rail
    "home": ("Home", "Giriş"),
    "new": ("New", "Yeni"),
    "open": ("Open", "Aç"),
    "account": ("Account", "Hesap"),
    "options": ("Options", "Seçenekler"),
    "back": ("Back", "Geri"),
    # Greeting
    "good_morning": ("Good morning", "Günaydın"),
    "good_afternoon": ("Good afternoon", "İyi günler"),
    "good_evening": ("Good evening", "İyi akşamlar"),
    # Home
    "blank_word": ("Blank document", "Boş belge"),
    "blank_sheet": ("Blank workbook", "Boş çalışma kitabı"),
    "blank_slides": ("Blank presentation", "Boş sunu"),
    "more_templates": ("More templates", "Daha fazla şablon"),
    "recent": ("Recent", "Son kullanılanlar"),
    "pinned": ("Pinned", "Sabitlenenler"),
    "search": ("Search", "Ara"),
    "search_templates": ("Search templates", "Şablonlarda ara"),
    "name": ("Name", "Ad"),
    "date_modified": ("Date modified", "Değiştirilme tarihi"),
    "no_recent": ("You haven't opened any documents recently. Click Open to browse for one.",
                  "Son zamanlarda belge açmadınız. Göz atmak için Aç'a tıklayın."),
    "no_recent_sheet": ("You haven't opened any workbooks recently. Click Open to browse for one.",
                        "Son zamanlarda çalışma kitabı açmadınız. Göz atmak için Aç'a tıklayın."),
    "no_recent_slides": ("You haven't opened any presentations recently. Click Open to browse for one.",
                         "Son zamanlarda sunu açmadınız. Göz atmak için Aç'a tıklayın."),
    "no_pinned": ("Pin files you want to find easily later. Click the pin icon that appears when "
                  "you hover over a file.",
                  "Daha sonra kolayca bulmak istediğiniz dosyaları sabitleyin. Bir dosyanın üzerine "
                  "geldiğinizde görünen raptiye simgesine tıklayın."),
    "no_results": ("No results for “{query}”", "“{query}” için sonuç yok"),
    "pin": ("Pin this item to the list", "Bu öğeyi listeye sabitle"),
    "unpin": ("Unpin this item from the list", "Bu öğenin sabitlemesini kaldır"),
    "remove_from_list": ("Remove from list", "Listeden kaldır"),
    "open_file_location": ("Open file location", "Dosya konumunu aç"),
    "copy_path": ("Copy path to clipboard", "Yolu panoya kopyala"),
    "today": ("Today", "Bugün"),
    "yesterday": ("Yesterday", "Dün"),
    "this_week": ("This week", "Bu hafta"),
    "last_week": ("Last week", "Geçen hafta"),
    "older": ("Older", "Daha eski"),
    "opening": ("Opening…", "Açılıyor…"),
    "missing_file": ("“{name}” could not be found. It may have been moved, renamed or deleted.",
                     "“{name}” bulunamadı. Taşınmış, yeniden adlandırılmış veya silinmiş olabilir."),
    # New page
    "new_title_word": ("New", "Yeni"),
    "templates": ("Templates", "Şablonlar"),
    "your_templates": ("Your templates", "Şablonlarınız"),
    "no_templates": ("No templates match your search.", "Aramanızla eşleşen şablon yok."),
    "create": ("Create", "Oluştur"),
    "provided_by": ("Provided by {source}", "{source} tarafından sağlandı"),
    "source_veltos": ("VeltOS", "VeltOS"),
    "source_libreoffice": ("LibreOffice", "LibreOffice"),
    "source_you": ("You", "Siz"),
    "preview": ("Preview", "Önizleme"),
    # Open page
    "this_pc": ("This PC", "Bu bilgisayar"),
    "browse": ("Browse", "Göz at"),
    "documents": ("Documents", "Belgeler"),
    "desktop": ("Desktop", "Masaüstü"),
    "downloads": ("Downloads", "İndirilenler"),
    "folders": ("Folders", "Klasörler"),
    "files": ("Files", "Dosyalar"),
    "open_dialog_title": ("Open", "Aç"),
    "filter_word": ("Documents", "Belgeler"),
    "filter_sheet": ("Workbooks", "Çalışma kitapları"),
    "filter_slides": ("Presentations", "Sunular"),
    "all_files": ("All files", "Tüm dosyalar"),
    # Account page
    "user_information": ("User Information", "Kullanıcı Bilgileri"),
    "local_account": ("Local account", "Yerel hesap"),
    "manage_account": ("Manage account", "Hesabı yönet"),
    "change_photo": ("Change photo", "Fotoğrafı değiştir"),
    "office_theme": ("Office Theme", "Office Teması"),
    "theme_colorful": ("Colorful", "Renkli"),
    "theme_dark": ("Dark", "Koyu"),
    "theme_system": ("Use system setting", "Sistem ayarını kullan"),
    "theme_note": ("The theme follows Settings > Personalization > Colors.",
                   "Tema, Ayarlar > Kişiselleştirme > Renkler'i izler."),
    "product_information": ("Product Information", "Ürün Bilgileri"),
    "about_text": ("VeltOS Office is LibreOffice {version}, set up for VeltOS. "
                   "Word, Excel and PowerPoint files open and save in their own formats.",
                   "VeltOS Office, VeltOS için ayarlanmış LibreOffice {version} sürümüdür. "
                   "Word, Excel ve PowerPoint dosyaları kendi biçimlerinde açılır ve kaydedilir."),
    # Options page
    "general": ("General", "Genel"),
    "start_up_options": ("Start up options", "Başlangıç seçenekleri"),
    "show_start_screen": ("Show the Start screen when this application starts",
                          "Bu uygulama başladığında Başlangıç ekranını göster"),
    "show_start_screen_note": ("Off: a blank document opens straight away.",
                               "Kapalı: doğrudan boş bir belge açılır."),
    "recent_files_options": ("Recent files", "Son kullanılan dosyalar"),
    "clear_recent": ("Clear the recent list", "Son kullanılanlar listesini temizle"),
    "clear_recent_note": ("Pinned files stay.", "Sabitlenen dosyalar kalır."),
    "clear": ("Clear", "Temizle"),
    "cleared": ("The list is empty.", "Liste boş."),
    "file_formats": ("File formats", "Dosya biçimleri"),
    "file_formats_note": ("New files are saved as .docx, .xlsx and .pptx. Change this in "
                          "Tools > Options > Load/Save > General inside the document window.",
                          "Yeni dosyalar .docx, .xlsx ve .pptx olarak kaydedilir. Bunu belge "
                          "penceresinde Araçlar > Seçenekler > Yükle/Kaydet > Genel'den değiştirin."),
    "more_options": ("More options", "Diğer seçenekler"),
    "more_options_note": ("Fonts, colours, language and everything else: in the document window, "
                          "Tools > Options.",
                          "Yazı tipleri, renkler, dil ve diğer her şey: belge penceresinde "
                          "Araçlar > Seçenekler."),
    "on": ("On", "Açık"),
    "off": ("Off", "Kapalı"),
    # Window
    "minimize": ("Minimize", "Simge durumuna küçült"),
    "maximize": ("Maximize", "Ekranı kapla"),
    "restore_down": ("Restore Down", "Aşağı geri yükle"),
    "close": ("Close", "Kapat"),
    "ok": ("OK", "Tamam"),
}

# Names of the templates that ship with LibreOffice (file name stem -> names).
TEMPLATE_NAMES = {
    "Modern_business_letter_sans_serif": ("Modern business letter (sans serif)", "Modern iş mektubu (sans serif)"),
    "Modern_business_letter_serif": ("Modern business letter (serif)", "Modern iş mektubu (serif)"),
    "Businesscard-with-logo": ("Business card with logo", "Logolu kartvizit"),
    "CV": ("Curriculum vitae", "Özgeçmiş (CV)"),
    "Resume1page": ("Résumé, one page", "Tek sayfalık özgeçmiş"),
    "Beehive": ("Beehive", "Arı kovanı"),
    "Blue_Curve": ("Blue curve", "Mavi kıvrım"),
    "Blueprint_Plans": ("Blueprint plans", "Teknik çizim"),
    "Candy": ("Candy", "Şeker"),
    "DNA": ("DNA", "DNA"),
    "Focus": ("Focus", "Odak"),
    "Forestbird": ("Forest bird", "Orman kuşu"),
    "Freshes": ("Freshes", "Taze"),
    "Grey_Elegant": ("Grey elegant", "Zarif gri"),
    "Growing_Liberty": ("Growing liberty", "Büyüyen özgürlük"),
    "Inspiration": ("Inspiration", "İlham"),
    "Lights": ("Lights", "Işıklar"),
    "Metropolis": ("Metropolis", "Metropol"),
    "Midnightblue": ("Midnight blue", "Gece mavisi"),
    "Nature_Illustration": ("Nature illustration", "Doğa çizimi"),
    "Pencil": ("Pencil", "Kurşun kalem"),
    "Piano": ("Piano", "Piyano"),
    "Portfolio": ("Portfolio", "Portföy"),
    "Progress": ("Progress", "İlerleme"),
    "Sunset": ("Sunset", "Gün batımı"),
    "Vintage": ("Vintage", "Nostaljik"),
    "Vivid": ("Vivid", "Canlı"),
    "Yellow_Idea": ("Yellow idea", "Sarı fikir"),
    # VeltOS' own templates (tools/make-templates.py)
    "Meeting_notes": ("Meeting notes", "Toplantı notları"),
    "Report": ("Report", "Rapor"),
    "To-do_list": ("To-do list", "Yapılacaklar listesi"),
    "Monthly_budget": ("Monthly budget", "Aylık bütçe"),
    "Invoice": ("Invoice", "Fatura"),
    "Expense_tracker": ("Expense tracker", "Harcama takibi"),
    "Weekly_schedule": ("Weekly schedule", "Haftalık program"),
}


def language(env=None):
    env = os.environ if env is None else env
    for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = env.get(key, "")
        if value:
            return "tr" if value.split(":")[0].lower().startswith("tr") else "en"
    return "en"


def text(lang, key, **values):
    pair = TEXTS[key]
    result = pair[1] if lang == "tr" else pair[0]
    return result.format(**values) if values else result


def app_title(lang, kind):
    pair = KINDS[kind]
    return pair[1] if lang == "tr" else pair[0]


def template_name(lang, stem):
    pair = TEMPLATE_NAMES.get(stem)
    if pair:
        return pair[1] if lang == "tr" else pair[0]
    return stem.replace("_", " ").replace("-", " ").strip()
