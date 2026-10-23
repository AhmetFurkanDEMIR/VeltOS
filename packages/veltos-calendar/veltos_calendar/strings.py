"""User interface texts of VeltOS Calendar (English and Turkish), in the
words of Windows 11's Calendar app."""

import os

TEXTS = {
    "app_title": ("Calendar", "Takvim"),
    "new_event": ("New event", "Yeni etkinlik"),
    "today": ("Today", "Bugün"),
    "day": ("Day", "Gün"),
    "work_week": ("Work week", "Çalışma haftası"),
    "week": ("Week", "Hafta"),
    "month": ("Month", "Ay"),
    "year": ("Year", "Yıl"),
    "previous": ("Previous", "Önceki"),
    "next": ("Next", "Sonraki"),
    "calendars": ("Calendars", "Takvimler"),
    "my_calendar": ("My calendar", "Takvimim"),
    "event_name": ("Event name", "Etkinlik adı"),
    "no_title": ("(No title)", "(Başlık yok)"),
    "location": ("Location", "Konum"),
    "add_location": ("Event location", "Etkinlik konumu"),
    "start": ("Start", "Başlangıç"),
    "end": ("End", "Bitiş"),
    "all_day": ("All day", "Tüm gün"),
    "repeat": ("Repeat", "Yinele"),
    "repeat_none": ("Doesn't repeat", "Yinelenmez"),
    "repeat_daily": ("Every day", "Her gün"),
    "repeat_weekly": ("Every week", "Her hafta"),
    "repeat_monthly": ("Every month", "Her ay"),
    "repeat_yearly": ("Every year", "Her yıl"),
    "reminder": ("Reminder", "Anımsatıcı"),
    "reminder_none": ("None", "Yok"),
    "reminder_0": ("At start time", "Başlangıç saatinde"),
    "reminder_minutes": ("{count} minutes before", "{count} dakika önce"),
    "reminder_hour": ("1 hour before", "1 saat önce"),
    "reminder_hours": ("{count} hours before", "{count} saat önce"),
    "reminder_day": ("1 day before", "1 gün önce"),
    "reminder_week": ("1 week before", "1 hafta önce"),
    "notes": ("Add a description", "Açıklama ekleyin"),
    "more_details": ("More details", "Diğer ayrıntılar"),
    "save": ("Save", "Kaydet"),
    "save_and_close": ("Save and close", "Kaydet ve kapat"),
    "delete": ("Delete", "Sil"),
    "edit": ("Edit", "Düzenle"),
    "cancel": ("Cancel", "İptal"),
    "close": ("Close", "Kapat"),
    "more_events": ("+{count} more", "+{count} daha"),
    "delete_question": ("Delete this event?", "Bu etkinlik silinsin mi?"),
    "delete_repeating": ("This event repeats. All its occurrences will be deleted.",
                         "Bu etkinlik yineleniyor. Tüm yinelemeleri silinecek."),
    "no_events": ("No events", "Etkinlik yok"),
    "reminder_title": ("Reminder: {title}", "Anımsatıcı: {title}"),
    "starts_now": ("Starts now", "Şimdi başlıyor"),
    "starts_at": ("Starts at {time}", "Başlangıç: {time}"),
    "starts_on": ("{date}, {time}", "{date}, {time}"),
    "dismiss": ("Dismiss", "Kapat"),
    "open": ("Open", "Aç"),
    "time_range": ("{start} – {end}", "{start} – {end}"),
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
