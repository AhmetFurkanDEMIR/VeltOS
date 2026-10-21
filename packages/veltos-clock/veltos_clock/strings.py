"""Texts of VeltOS Clock (English and Turkish), in the words of Windows
11's Clock app."""

import os

TEXTS = {
    "app_title": ("Clock", "Saat"),
    "focus": ("Focus sessions", "Odaklanma oturumları"),
    "timer": ("Timer", "Zamanlayıcı"),
    "alarm": ("Alarm", "Alarm"),
    "stopwatch": ("Stopwatch", "Kronometre"),
    "world": ("World clock", "Dünya saati"),
    # Alarm
    "no_alarms": ("No alarms yet. Add one with +.", "Henüz alarm yok. + ile ekleyin."),
    "add_alarm": ("Add an alarm", "Alarm ekle"),
    "edit_alarm": ("Edit alarm", "Alarmı düzenle"),
    "alarm_name": ("Alarm name", "Alarm adı"),
    "repeat": ("Repeat alarm", "Alarmı yinele"),
    "snooze_time": ("Snooze time", "Erteleme süresi"),
    "minutes_short": ("{n} minutes", "{n} dakika"),
    "save": ("Save", "Kaydet"),
    "cancel": ("Cancel", "İptal"),
    "delete": ("Delete", "Sil"),
    "rings_in": ("in {time}", "{time} sonra"),
    "off": ("Off", "Kapalı"),
    "hours_minutes": ("{h} h {m} min", "{h} sa {m} dk"),
    "minutes_only": ("{m} min", "{m} dk"),
    "days_hours": ("{d} d {h} h", "{d} g {h} sa"),
    # Timer
    "no_timers": ("No timers yet. Add one with +.", "Henüz zamanlayıcı yok. + ile ekleyin."),
    "add_timer": ("Add a timer", "Zamanlayıcı ekle"),
    "edit_timer": ("Edit timer", "Zamanlayıcıyı düzenle"),
    "timer_name": ("Timer name", "Zamanlayıcı adı"),
    "hours": ("Hours", "Saat"),
    "minutes": ("Minutes", "Dakika"),
    "seconds": ("Seconds", "Saniye"),
    "start": ("Start", "Başlat"),
    "pause": ("Pause", "Duraklat"),
    "reset": ("Reset", "Sıfırla"),
    "resume": ("Resume", "Sürdür"),
    "timer_done": ("Time's up", "Süre doldu"),
    # Stopwatch
    "lap": ("Lap", "Tur"),
    "laps": ("Laps", "Turlar"),
    "lap_time": ("Lap time", "Tur süresi"),
    "total": ("Total", "Toplam"),
    # World clock
    "no_clocks": ("Add a city with + to see its time.", "Saatini görmek için + ile bir şehir ekleyin."),
    "add_clock": ("Add a clock", "Saat ekle"),
    "search_city": ("Enter a location", "Bir konum girin"),
    "local_time": ("Local time", "Yerel saat"),
    "same_time": ("Same as local time", "Yerel saatle aynı"),
    "hours_ahead": ("{h} hours ahead", "{h} saat ileride"),
    "hour_ahead": ("1 hour ahead", "1 saat ileride"),
    "hours_behind": ("{h} hours behind", "{h} saat geride"),
    "hour_behind": ("1 hour behind", "1 saat geride"),
    "today": ("Today", "Bugün"),
    "tomorrow": ("Tomorrow", "Yarın"),
    "yesterday": ("Yesterday", "Dün"),
    # Focus
    "focus_title": ("Get ready to focus", "Odaklanmaya hazırlanın"),
    "focus_desc": ("Notifications are quiet while a session runs. Pick how long you want to work.",
                   "Oturum sürerken bildirimler sessiz kalır. Ne kadar çalışmak istediğinizi seçin."),
    "session_length": ("Session length", "Oturum süresi"),
    "start_focus": ("Start focus session", "Odaklanma oturumunu başlat"),
    "end_focus": ("End session", "Oturumu bitir"),
    "focus_running": ("Focus session", "Odaklanma oturumu"),
    "focus_done": ("Focus session finished", "Odaklanma oturumu bitti"),
    "focus_done_body": ("Well done. Time for a break.", "Aferin. Mola zamanı."),
    # Agent notifications
    "alarm_notification": ("Alarm", "Alarm"),
    "snooze": ("Snooze", "Ertele"),
    "dismiss": ("Dismiss", "Kapat"),
    "timer_notification": ("Timer", "Zamanlayıcı"),
    "timer_body": ("{name} is done.", "{name} tamamlandı."),
    "unnamed_timer": ("Timer", "Zamanlayıcı"),
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
