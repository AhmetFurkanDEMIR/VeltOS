"""Texts of VeltOS Weather (English and Turkish), in the words of Windows
11's Weather app."""

import os

TEXTS = {
    "app_title": ("Weather", "Hava Durumu"),
    # Navigation
    "forecast": ("Forecast", "Tahmin"),
    "history": ("Historical weather", "Geçmiş hava durumu"),
    "favorites": ("Favorites", "Sık kullanılanlar"),
    "settings": ("Settings", "Ayarlar"),
    # Search and places
    "search": ("Search for location", "Konum arayın"),
    "no_results": ("No places found", "Konum bulunamadı"),
    "searching": ("Searching…", "Aranıyor…"),
    "add_favorite": ("Add to favorites", "Sık kullanılanlara ekle"),
    "remove_favorite": ("Remove from favorites", "Sık kullanılanlardan kaldır"),
    "set_home": ("Set as home", "Ana konum yap"),
    "home": ("Home", "Ana konum"),
    "no_favorites": ("Search for a place and add it to your favorites with the star.",
                     "Bir konum arayın ve yıldızla sık kullanılanlarınıza ekleyin."),
    "first_place": ("Search for a city to see its weather.", "Hava durumunu görmek için bir şehir arayın."),
    # Current weather
    "current_weather": ("Current weather", "Güncel hava durumu"),
    "feels_like": ("Feels like", "Hissedilen"),
    "air_quality": ("Air quality", "Hava kalitesi"),
    "wind": ("Wind", "Rüzgar"),
    "humidity": ("Humidity", "Nem"),
    "visibility": ("Visibility", "Görüş mesafesi"),
    "pressure": ("Pressure", "Basınç"),
    "dew_point": ("Dew point", "Çiy noktası"),
    "uv_index": ("UV index", "UV dizini"),
    "precipitation": ("Precipitation", "Yağış"),
    "cloud_cover": ("Cloud cover", "Bulut örtüsü"),
    "updated": ("Updated {time}", "Güncellendi: {time}"),
    "refresh": ("Refresh", "Yenile"),
    "summary": ("{condition}. The high will be {high}, the low {low}.",
                "{condition}. En yüksek {high}, en düşük {low} olacak."),
    "summary_rain": (" Precipitation is likely ({chance}).", " Yağış bekleniyor ({chance})."),
    "summary_night": ("{condition}. The low tonight will be {low}.", "{condition}. Gece en düşük {low} olacak."),
    # Forecast
    "daily_forecast": ("10-day forecast", "10 günlük tahmin"),
    "today": ("Today", "Bugün"),
    "tonight": ("Tonight", "Bu gece"),
    "now": ("Now", "Şimdi"),
    "hourly": ("Hourly forecast", "Saatlik tahmin"),
    "overview": ("Overview", "Genel bakış"),
    "weather_details": ("Weather details", "Hava durumu ayrıntıları"),
    "chance": ("Chance of precipitation", "Yağış olasılığı"),
    "gusts": ("Gusts {speed}", "Hamle {speed}"),
    "from_direction": ("From {direction}", "{direction} yönünden"),
    # Sun and moon
    "sun": ("Sun", "Güneş"),
    "sunrise": ("Sunrise", "Gün doğumu"),
    "sunset": ("Sunset", "Gün batımı"),
    "daylight": ("{h} h {m} min of daylight", "{h} sa {m} dk gün ışığı"),
    "moon": ("Moon", "Ay"),
    "illumination": ("{percent} illuminated", "{percent} aydınlık"),
    "moon_new": ("New moon", "Yeni ay"),
    "moon_waxing_crescent": ("Waxing crescent", "Büyüyen hilal"),
    "moon_first_quarter": ("First quarter", "İlk dördün"),
    "moon_waxing_gibbous": ("Waxing gibbous", "Büyüyen şişkin ay"),
    "moon_full": ("Full moon", "Dolunay"),
    "moon_waning_gibbous": ("Waning gibbous", "Küçülen şişkin ay"),
    "moon_last_quarter": ("Last quarter", "Son dördün"),
    "moon_waning_crescent": ("Waning crescent", "Küçülen hilal"),
    # Bands
    "aqi_good": ("Good", "İyi"),
    "aqi_fair": ("Fair", "Makul"),
    "aqi_moderate": ("Moderate", "Orta"),
    "aqi_poor": ("Poor", "Kötü"),
    "aqi_very_poor": ("Very poor", "Çok kötü"),
    "aqi_extremely_poor": ("Extremely poor", "Son derece kötü"),
    "aqi_text_good": ("Air quality is good. Enjoy your usual outdoor activities.",
                      "Hava kalitesi iyi. Açık havadaki etkinliklerinizin keyfini çıkarın."),
    "aqi_text_fair": ("Air quality is acceptable for most people.", "Hava kalitesi çoğu kişi için kabul edilebilir."),
    "aqi_text_moderate": ("Sensitive people should consider less time outdoors.",
                          "Hassas kişiler dışarıda daha az zaman geçirmeyi düşünmeli."),
    "aqi_text_poor": ("Consider reducing intense activities outdoors.",
                      "Açık havada yoğun etkinlikleri azaltmayı düşünün."),
    "aqi_text_very_poor": ("Reduce physical activities outdoors.", "Açık havadaki fiziksel etkinlikleri azaltın."),
    "aqi_text_extremely_poor": ("Avoid physical activities outdoors.", "Açık havada fiziksel etkinliklerden kaçının."),
    "uv_low": ("Low", "Düşük"),
    "uv_moderate": ("Moderate", "Orta"),
    "uv_high": ("High", "Yüksek"),
    "uv_very_high": ("Very high", "Çok yüksek"),
    "uv_extreme": ("Extreme", "Aşırı"),
    "uv_text_low": ("No protection needed.", "Koruma gerekmez."),
    "uv_text_moderate": ("Wear sunglasses and sunscreen at midday.", "Öğle saatlerinde güneş gözlüğü ve kremi kullanın."),
    "uv_text_high": ("Protection needed: seek shade at midday.", "Koruma gerekli: öğle saatlerinde gölgede kalın."),
    "uv_text_very_high": ("Extra protection needed.", "Ek koruma gerekli."),
    "uv_text_extreme": ("Avoid being outside at midday.", "Öğle saatlerinde dışarıda olmaktan kaçının."),
    "humidity_dry": ("The air is dry.", "Hava kuru."),
    "humidity_comfortable": ("The air feels comfortable.", "Hava rahat hissettiriyor."),
    "humidity_humid": ("The air feels humid.", "Hava nemli hissettiriyor."),
    "visibility_good": ("Clear view.", "Görüş açık."),
    "visibility_moderate": ("Hazy view.", "Görüş puslu."),
    "visibility_poor": ("Poor visibility.", "Görüş zayıf."),
    "pressure_rising": ("Rising", "Yükseliyor"),
    "pressure_falling": ("Falling", "Düşüyor"),
    "pressure_steady": ("Steady", "Sabit"),
    "feels_colder": ("Wind and humidity make it feel colder.", "Rüzgar ve nem daha soğuk hissettiriyor."),
    "feels_warmer": ("Humidity makes it feel warmer.", "Nem daha sıcak hissettiriyor."),
    "feels_same": ("Similar to the actual temperature.", "Gerçek sıcaklığa yakın."),
    "precip_today": ("{amount} expected today.", "Bugün {amount} bekleniyor."),
    "precip_none": ("No precipitation expected today.", "Bugün yağış beklenmiyor."),
    # Conditions (WMO codes)
    "clear": ("Clear", "Açık"),
    "sunny": ("Sunny", "Güneşli"),
    "mostly_clear": ("Mostly clear", "Çoğunlukla açık"),
    "mostly_sunny": ("Mostly sunny", "Çoğunlukla güneşli"),
    "partly_cloudy": ("Partly cloudy", "Parçalı bulutlu"),
    "cloudy": ("Cloudy", "Bulutlu"),
    "fog": ("Fog", "Sis"),
    "light_drizzle": ("Light drizzle", "Hafif çisenti"),
    "drizzle": ("Drizzle", "Çisenti"),
    "freezing_drizzle": ("Freezing drizzle", "Dondurucu çisenti"),
    "light_rain": ("Light rain", "Hafif yağmur"),
    "rain": ("Rain", "Yağmur"),
    "heavy_rain": ("Heavy rain", "Şiddetli yağmur"),
    "freezing_rain": ("Freezing rain", "Dondurucu yağmur"),
    "light_snow": ("Light snow", "Hafif kar"),
    "snow": ("Snow", "Kar"),
    "heavy_snow": ("Heavy snow", "Yoğun kar"),
    "snow_grains": ("Snow grains", "Kar taneleri"),
    "rain_showers": ("Rain showers", "Sağanak yağmur"),
    "heavy_showers": ("Heavy rain showers", "Kuvvetli sağanak"),
    "snow_showers": ("Snow showers", "Kar sağanağı"),
    "thunderstorm": ("Thunderstorms", "Gök gürültülü fırtına"),
    "thunderstorm_hail": ("Thunderstorms with hail", "Dolulu gök gürültülü fırtına"),
    # History
    "history_title": ("Monthly averages", "Aylık ortalamalar"),
    "history_desc": ("Averages of the last five years, from weather records.",
                     "Son beş yılın kayıtlarından ortalamalar."),
    "avg_high": ("Average high", "Ortalama en yüksek"),
    "avg_low": ("Average low", "Ortalama en düşük"),
    "avg_precip": ("Average precipitation", "Ortalama yağış"),
    "rainy_days": ("Days with precipitation", "Yağışlı gün sayısı"),
    "record_high": ("Highest", "En yüksek"),
    "record_low": ("Lowest", "En düşük"),
    "days_value": ("{n} days", "{n} gün"),
    # Settings
    "temperature_unit": ("Temperature", "Sıcaklık"),
    "fahrenheit": ("Fahrenheit", "Fahrenhayt"),
    "celsius": ("Celsius", "Santigrat"),
    "launch_location": ("Launch location", "Başlangıç konumu"),
    "launch_location_desc": ("The weather of your home place is shown when the app starts.",
                             "Uygulama açıldığında ana konumunuzun hava durumu gösterilir."),
    "about": ("About", "Hakkında"),
    "about_text": ("VeltOS Weather shows forecasts of Open-Meteo, an open-source weather service, without an "
                   "account or a key. Weather data © Open-Meteo.com, licensed under CC BY 4.0. Places: GeoNames.",
                   "VeltOS Hava Durumu, açık kaynaklı hava durumu hizmeti Open-Meteo'nun tahminlerini hesap ya da "
                   "anahtar olmadan gösterir. Hava durumu verileri © Open-Meteo.com, CC BY 4.0 lisanslı. Konumlar: "
                   "GeoNames."),
    "attribution": ("Weather data: Open-Meteo.com (CC BY 4.0)", "Hava durumu verileri: Open-Meteo.com (CC BY 4.0)"),
    # Errors
    "offline": ("Can't get the weather right now. Check your internet connection.",
                "Şu anda hava durumu alınamıyor. İnternet bağlantınızı denetleyin."),
    "showing_saved": ("Showing the last saved weather.", "Son kaydedilen hava durumu gösteriliyor."),
    "try_again": ("Try again", "Yeniden dene"),
    "loading": ("Getting the weather…", "Hava durumu alınıyor…"),
}

WIND_DIRECTIONS = {
    "en": ("N", "NE", "E", "SE", "S", "SW", "W", "NW"),
    "tr": ("K", "KD", "D", "GD", "G", "GB", "B", "KB"),
}

MONTHS = {
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
    "tr": ("Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"),
}

DAYS = {   # Monday first, as datetime.weekday()
    "en": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
    "tr": ("Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"),
}

LONG_DAYS = {
    "en": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    "tr": ("Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"),
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
