/* VeltOS website: language (English in the page, Turkish here), theme,
   menu, appear-on-scroll, gallery, lightbox and the download. No external
   requests; the page works from file:// too. */
(function () {
  "use strict";

  var TR = {
    "skip": "İçeriğe geç",
    "aria.main": "Ana menü",
    "aria.stats": "Rakamlarla VeltOS",
    "aria.footer": "Bağlantılar",
    "nav.features": "Özellikler",
    "nav.ai": "VeltOS AI",
    "nav.apps": "Uygulamalar",
    "nav.gallery": "Ekran görüntüleri",
    "nav.windows": "Windows uygulamaları",
    "nav.faq": "SSS",
    "nav.download": "İndir",
    "nav.menu": "Menü",
    "theme.toggle": "Açık veya koyu",

    "hero.eyebrow": "Sürüm 1.0 · Ücretsiz ve açık kaynak · Debian 13 tabanlı",
    "hero.title1": "Senin Bilgisayarın.",
    "hero.title2": "Sınır Tanıma.",
    "hero.lead": "VeltOS, Windows 11 kullanıcılarının zaten bildiği gibi çalışan ücretsiz bir işletim sistemidir: Başlat, görev çubuğu, Dosya Gezgini, Ayarlar ve mağaza tam beklediğiniz yerde. Yirmiden fazla kendi uygulaması, VeltOS AI yardımcısı, Office, modern bir kurulum programı ve Windows programı desteğiyle gelir.",
    "hero.download": "VeltOS'u indir",
    "hero.source": "Kaynak kodu",
    "hero.meta": "64 bit bilgisayarlar · 2,1 GB ISO · Türkçe ve English · Her zaman ücretsiz",
    "hero.float.ai": "Windows + C · yardıma hazır",
    "hero.float.sec1": "Güvenli Önyükleme · AppArmor",
    "hero.float.sec2": "Yalnızca imzalı yazılım",
    "hero.float.win1": "Windows programları",
    "hero.float.win2": "Kurmak için .exe'ye çift tıklayın",
    "alt.hero.dark": "Koyu modda, Başlat menüsü açık VeltOS masaüstü",
    "alt.hero.light": "Açık modda, Başlat menüsü açık VeltOS masaüstü",

    "stat.boot": "oturum açma ekranına kadar açılış*",
    "stat.apps": "kendi uygulaması",
    "stat.tests": "her derlemede otomatik test",
    "stat.free": "ücretsiz ve açık kaynak",
    "stats.note": "* Kurulu bir VeltOS 1.0'da (4 işlemci çekirdeği, 8 GB bellek) systemd-analyze ile ölçülmüştür: çekirdekten oturum açma ekranına kadar geçen süre, bilgisayarın üretici yazılımı hariç. Sizin donanımınızda farklı olacaktır.",

    "features.kicker": "Özellikler",
    "features.title": "Her şey beklediğiniz yerde",
    "features.lead": "Yeniden öğrenmeye gerek yok: VeltOS, Windows 11'den bildiğiniz yerleri, adları ve kısayolları hızlı ve güvenli, açık kaynaklı bir temel üzerinde korur.",
    "f1.t": "Zaten bildiğiniz bir masaüstü",
    "f1.d": "Ortalanmış görev çubuğu, sabitlenmiş uygulamalarıyla Başlat, yazdıkça arama, sanal masaüstleriyle Görev Görünümü, bildirim merkezi ve bildiğiniz sağ tık menüleri.",
    "f2.t": "Dosya Gezgini",
    "f2.d": "Sekmeler, Giriş, Bu bilgisayar ve Geri Dönüşüm Kutusu. USB bellekler ve Windows sürücüleri olduğu gibi açılır; kopyalama, sıkıştırma ve biçimlendirme sağ tık menüsünde.",
    "f3.t": "Tüm ayarlar tek yerde",
    "f3.d": "Wi-Fi, Bluetooth, sürükleyerek yerleştirdiğiniz ekranlar, ses, hesaplar, temalar ve vurgu renkleri; hepsi Windows 11'in tanıdık sayfalarında.",
    "f4.t": "Hızlı Ayarlar",
    "f4.d": "Wi-Fi, Bluetooth, mobil etkin nokta, gece ışığı, güç modları, ses ve parlaklık tek panelde. Windows + P ile ikinci ekrana yansıtın.",
    "f5.t": "VeltOS Mağaza",
    "f5.d": "Debian'ın imzalı arşivinden binlerce ücretsiz uygulama ve oyun, tek tıkla kurulur. Güncelleştirmeler de aynı yerden gelir.",
    "f6.t": "Office, çalışmaya hazır",
    "f6.d": "Word, Excel ve PowerPoint belgeleri VeltOS Office'te açılır ve varsayılan olarak Microsoft biçimlerinde kaydedilir; başlamak için şablonlar hazır.",
    "f7.t": "Windows programları",
    "f7.d": "Bir .exe veya .msi dosyasına çift tıklayın; VeltOS onu Wine ile kurar ve Başlat'a ekler. Her program çalışmaz; VeltOS bunu size söyler.",
    "f8.t": "Tek düğmeyle sürücüler",
    "f8.d": "Ekran Kartları uygulaması kartlarınızı gösterir ve NVIDIA sürücüsünü ya da AMD ve Intel üretici yazılımını Debian'ın arşivinden tek düğmeyle kurar.",
    "f9.t": "Otomatik Onarım",
    "f9.d": "VeltOS üst üste iki kez başlayamazsa Otomatik Onarım açılır: Başlangıç Onarımı, güvenli mod ve Komut İstemi. Açılışta F1 önyükleme menüsünü, F6 Kurtarma'yı açar.",
    "f10.t": "Varsayılan olarak güvenli",
    "f10.d": "Yalnızca imzalı arşivlerden yazılım, AppArmor, Güvenli Önyükleme, açılışta parolanızı soran disk şifrelemesi ve Kullanıcı Hesabı Denetimi gibi bir yönetici onayı.",
    "f11.t": "Hafif ve hızlı",
    "f11.d": "Az sayıda arka plan hizmeti, Windows 11'deki gibi bellek sıkıştırma ve oturum açma ekranına yaklaşık dört saniyelik açılış.",
    "f12.t": "Anlaşılır bir kurulum",
    "f12.d": "Windows 11 tarzında kurulum: Windows'un yanına ya da yerine, isterseniz şifreli, birkaç dakikada ve kendi dilinizde.",

    "ai.title": "Masaüstünüzde bir yardımcı",
    "ai.lead": "Windows + C'ye basın, VeltOS AI tıpkı Copilot gibi çalışmanızın yanında açılsın. Bir soru sorun, e-posta yazdırın ya da bir ayarı sizin için değiştirsin: her zaman önce size sorar.",
    "ai.p1": "Kendi API anahtarınızla ChatGPT, Claude, Gemini veya Copilot; anahtarınız bilgisayarınızda kalır.",
    "ai.p2": "Ya da bilgisayarınızda internetsiz çalışan ücretsiz bir model: yazdıklarınız bilgisayarınızdan çıkmaz.",
    "ai.p3": "Değişiklikleri yalnızca İzin ver'e bastığınızda yapar: koyu mod, Bluetooth, Wi-Fi, gece ışığı ve daha fazlası.",
    "ai.p4": "Türkçe, İngilizce ve birçok başka dilde yanıt verir.",
    "alt.ai": "Masaüstünün sağındaki panelde yanıt veren VeltOS AI",

    "modes.kicker": "Kişiselleştirme",
    "modes.title": "Açık, koyu ve sizin renginiz",
    "modes.lead": "Ayarlar'dan açık ve koyu mod arasında geçiş yapın ya da VeltOS AI'dan isteyin. Tüm uygulamalar sekiz tema, duvar kağıtları ve seçtiğiniz vurgu rengiyle birlikte buna uyar.",
    "modes.p1": "Tüm VeltOS uygulamalarında, görev çubuğunda ve Başlat'ta Windows 11 görünümü.",
    "modes.p2": "Ekranlar, ölçekleme ve gece ışığı Ayarlar › Sistem › Ekran'da.",
    "alt.modes": "Açık ve koyu mod arasında geçen Ayarlar ve Fotoğraflar (VeltOS'ta kaydedilmiş animasyon)",

    "apps.kicker": "Uygulamalar",
    "apps.title": "Yirmiden fazla kendi uygulaması",
    "apps.lead": "Her biri Windows 11'deki karşılığının düzeninde; Türkçe ve İngilizce, açık ve koyu modda. Firefox, LibreOffice ve binlercesi de Mağaza'dan gelir.",
    "app.explorer": "Dosya Gezgini",
    "app.settings": "Ayarlar",
    "app.store": "VeltOS Mağaza",
    "app.calendar": "Takvim",
    "app.clock": "Saat",
    "app.weather": "Hava Durumu",
    "app.maps": "Haritalar",
    "app.photos": "Fotoğraflar",
    "app.media": "Medya Oynatıcı",
    "app.camera": "Kamera",
    "app.snip": "Ekran Alıntısı Aracı",
    "app.calculator": "Hesap Makinesi",
    "app.notepad": "Not Defteri",
    "app.pdf": "PDF Okuyucu",
    "app.archive": "Arşiv",
    "app.taskmanager": "Görev Yöneticisi",
    "app.disks": "Disk Yönetimi",
    "app.graphics": "Ekran Kartları",
    "app.winapps": "Windows programları",
    "alt.tour.apps": "Dosya Gezgini, Word, Medya Oynatıcı, Hava Durumu, Takvim ve Görev Yöneticisi (VeltOS'ta kaydedilmiş animasyon)",

    "gallery.kicker": "Ekran görüntüleri",
    "gallery.title": "Kendiniz görün",
    "gallery.lead": "Tüm görüntüler VeltOS 1.0'da alındı. İki görünümü de görmek için bu sayfayı açık ve koyu mod arasında değiştirin; büyütmek için bir görüntüye tıklayın.",
    "gallery.tabs": "Ekran görüntüleri",
    "gallery.prev": "Önceki",
    "gallery.next": "Sonraki",
    "zoom.open": "Büyüt",
    "shot.desktop": "Masaüstü",
    "shot.quick": "Hızlı Ayarlar",
    "cap.desktop": "Sabitlenmiş uygulamalar, öneriler ve kategorilere ayrılmış tüm uygulamalarla Başlat.",
    "cap.explorer": "Sekmeleri, Giriş'i ve hızlı erişimiyle Dosya Gezgini.",
    "cap.settings": "Windows 11'deki gibi Ayarlar'ın Giriş sayfası.",
    "cap.quick": "Görev çubuğunda Hızlı Ayarlar: ağlar, Bluetooth, etkin nokta, gece ışığı ve güç modları.",
    "cap.ai": "Ücretsiz yerel modelle e-posta yazan VeltOS AI.",
    "cap.store": "Debian'ın imzalı arşivindeki uygulamalarıyla VeltOS Mağaza.",
    "cap.word": "Şablonlarıyla Word'ün başlangıç ekranı.",
    "cap.photos": "Fotoğraflar: resimleriniz aylara göre.",
    "cap.media": "Albümleri ve kapaklarıyla Medya Oynatıcı.",
    "cap.weather": "Hesap gerektirmeyen, 10 günlük tahminli Hava Durumu.",
    "cap.calendar": "Gün, hafta, ay ve yıl görünümleri ve anımsatıcılarıyla Takvim.",
    "cap.taskmanager": "Görev Yöneticisi: işlemler, performans ve başlangıç uygulamaları.",
    "start.title": "Açılıştan masaüstünüze",
    "start.lead": "Önyükleme menüsü yok, yazı yok: VeltOS'un açılış ekranı, oturum açma ekranı ve masaüstünüz. F1 önyükleme menüsünü, F6 Kurtarma'yı açar.",
    "cap.boot": "Açılış ekranı",
    "cap.lock": "Oturum açma ekranı",
    "cap.password": "Hesabınız",
    "cap.welcome": "Hoş geldiniz",
    "cap.repair": "Otomatik Onarım",
    "tour.title": "VeltOS ile bir dakika",
    "tour.lead": "Başlat, arama, Görev Görünümü ve VeltOS AI; VeltOS'ta kaydedildi.",
    "alt.tour.desktop": "Başlat, arama, Görev Görünümü ve VeltOS AI (VeltOS'ta kaydedilmiş animasyon)",

    "win.kicker": "Windows programları",
    "win.title": "Windows programlarınız, çift tıkla",
    "win.lead": "Dosya Gezgini'nde bir .exe veya .msi dosyasını açın: VeltOS, Wine'ı hazırlar, programı kurar ve Windows'un Uygulama Yükleyicisi'ne benzeyen bir pencereyle Başlat'a ekler.",
    "win.p1": "Programlar Başlat'ta görünür; onları Ayarlar › Uygulamalar'dan kaldırırsınız.",
    "win.p2": "Wine 10, Wine Mono, Gecko ve Direct3D oyunları için DXVK; hepsi imzalı arşivlerden.",
    "win.p3": "Her program çalışmaz: hile önleyicili oyunlar ve kendi sürücüsünü isteyen programlar genellikle çalışmaz. Bir program çalışmadığında VeltOS size söyler.",
    "win.p4": "Wine bir güvenlik korumalı alanı değildir: yalnızca güvendiğiniz programları çalıştırın, asla yönetici olarak değil.",
    "win.card.t": "7-Zip",
    "win.card.d": "Kuruldu · Başlat'ta",

    "inst.kicker": "Kurulum",
    "inst.title": "Birkaç dakikada kurulur",
    "inst.lead": "VeltOS'un kurulum programı Windows 11 kurulumuna benzer ve her adımı açıklar. Windows'un yanına, yerine ya da boş bir bölüme kurun; isterseniz diski şifreleyin.",
    "cap.inst1": "Dilinizi seçin",
    "cap.inst2": "Kurulurken VeltOS'u tanıyın",
    "cap.inst3": "VeltOS hazır",

    "specs.kicker": "Teknik ayrıntılar",
    "s.title": "Sürüm 1.0: kendini kanıtlamış yazılımlar üzerine kurulu",
    "s.version": "Sürüm",
    "s.version.v": "1.0 (27 Ekim 2026)",
    "s.base": "Temel",
    "s.kernel": "Çekirdek",
    "s.kernel.v": "Linux 6.12 LTS, Güvenli Önyükleme için imzalı",
    "s.desktop": "Masaüstü",
    "s.desktop.v": "Wayland üzerinde KDE Plasma 6.3; VeltOS'un görev çubuğu, Başlat'ı ve pencere çerçeveleriyle",
    "s.apps": "VeltOS uygulamaları",
    "s.office": "Office, web",
    "s.windows": "Windows programları",
    "s.boot": "Açılış",
    "s.boot.v": "UEFI ve BIOS, Güvenli Önyükleme, GRUB 2.12, Otomatik Onarım",
    "s.lang": "Diller",
    "s.lang.v": "VeltOS uygulamalarında Türkçe ve İngilizce; sistemde çok daha fazlası",
    "s.iso": "ISO",
    "s.iso.v": "2,1 GB; USB bellek ve DVD için tek bir hibrit görüntü",
    "s.licence": "Lisans",
    "s.licence.v": "GPL-3.0-or-later (görseller CC BY-SA 4.0)",

    "d.kicker": "İndir",
    "d.title": "VeltOS 1.0'ı indirin",
    "d.lead": "64 bit bilgisayarlar için tek bir ISO dosyası hem canlı sistem olarak açılır hem de VeltOS'u kurar. Önce canlı olarak deneyin, sonra Windows'un yanına ya da yerine kurun.",
    "dl.badge": "ilk sürüm",
    "dl.meta": "VeltOS-1.0-amd64.iso · 2,1 GB · 64 bit",
    "dl.button": "ISO'yu indir",
    "dl.release": "Sürüm notları ve tüm dosyalar GitHub'da ›",
    "d.copy": "Kopyala",
    "d.copied": "Kopyalandı",
    "dl.hashnote": "İndirdikten sonra doğrulayın: Linux'ta <code>sha256sum VeltOS-1.0-amd64.iso</code>, PowerShell'de <code>Get-FileHash VeltOS-1.0-amd64.iso</code>.",
    "dl.inc.title": "ISO'nun içinde",
    "dl.inc1": "Canlı sistem: hiçbir şey kurmadan VeltOS'u deneyin",
    "dl.inc2": "Kurulum programı: Windows'un yanına, yerine ya da boş alana",
    "dl.inc3": "Gereken her şey: internet bağlantısı olmadan kurulur",
    "dl.inc4": "UEFI, BIOS ve Güvenli Önyükleme ile açılır",
    "dl.s1.t": "ISO'yu indirin",
    "dl.s1.d": "Tüm 64 bit bilgisayarlar için tek dosya, yaklaşık 2,1 GB.",
    "dl.s2.t": "USB belleğe yazın",
    "dl.s2.d": "Windows'ta Rufus veya balenaEtcher kullanın (balenaEtcher macOS ve Linux'ta da var). 4 GB veya daha büyük bir bellek yeterli.",
    "dl.s3.t": "Bilgisayarınızı ondan başlatın",
    "dl.s3.d": "Bilgisayarınızın önyükleme menüsünde USB belleği seçin (çoğunlukla F12, F11 veya Esc). VeltOS canlı sistem olarak açılır; önce göz atabilirsiniz.",
    "dl.s4.t": "VeltOS'u kurun",
    "dl.s4.d": "“VeltOS'u Kur”u seçin ve adımları izleyin. Her yeni sistemde olduğu gibi önce dosyalarınızı yedekleyin.",
    "r.title": "Bilgisayarınızın ihtiyaçları",
    "r.cpu.t": "İşlemci",
    "r.cpu.d": "64 bit Intel veya AMD",
    "r.ram.t": "Bellek",
    "r.ram.d": "En az 2 GB, 4 GB veya daha fazlası önerilir",
    "r.disk.t": "Depolama",
    "r.disk.d": "20 GB veya daha fazla",
    "r.boot.t": "Üretici yazılımı",
    "r.boot.d": "UEFI (Güvenli Önyükleme açık veya kapalı) veya BIOS",
    "r.note": "UEFI, BIOS ve Güvenli Önyükleme ile test edildi ve NVIDIA ekran kartlı bir dizüstü bilgisayara kuruldu.",

    "faq.kicker": "SSS",
    "faq.title": "Sorular ve yanıtlar",
    "q.1.q": "VeltOS ücretsiz mi?",
    "q.1.a": "Evet. VeltOS ücretsiz ve açık kaynaktır (GPL-3.0-or-later); parçaları Debian'dan ve diğer açık kaynak projelerden gelir. Reklam ve hesap zorunluluğu yoktur.",
    "q.2.q": "VeltOS bir Windows mu?",
    "q.2.a": "Hayır. VeltOS, KDE Plasma kullanan, Debian 13 tabanlı bir Linux dağıtımıdır. Windows 11 gibi görünür ve çalışır ancak Microsoft kodu içermez ve Microsoft ile bağlantılı değildir.",
    "q.3.q": "Windows programlarım çalışır mı?",
    "q.3.a": "VeltOS'un çift tıkla kurduğu Wine sayesinde birçoğu çalışır. Her program çalışmaz; özellikle hile önleyicili oyunlar ve kendi sürücüsünü isteyen programlar. Wine bir güvenlik korumalı alanı değildir.",
    "q.4.q": "Windows'u koruyabilir miyim?",
    "q.4.a": "Evet. Kurulum programı VeltOS'u Windows'un yanına kurabilir. Bilgisayar açılırken ikisi arasında seçim yapmak için F1'e basın; basmazsanız VeltOS açılır.",
    "q.5.q": "Günlük kullanıma hazır mı?",
    "q.5.a": "VeltOS 1.0, herkese açık ilk sürümdür. Her yeni sistemde olduğu gibi kurmadan önce dosyalarınızı yedekleyin ve çalışmayan bir şey görürseniz GitHub'da bildirin.",
    "q.6.q": "Güncelleştirmeler nasıl geliyor?",
    "q.6.a": "Güvenlik ve uygulama güncelleştirmeleri Debian'ın imzalı arşivinden gelir; VeltOS Mağaza bunları gösterir ve kurar.",
    "q.7.q": "VeltOS AI verilerimi bir yere gönderiyor mu?",
    "q.7.a": "Çevrimiçi bir hizmet seçtiyseniz mesajlarınız kendi anahtarınızla seçtiğiniz hizmete gider. Ücretsiz yerel model tamamen bilgisayarınızda çalışır; yazdıklarınız bilgisayarınızdan çıkmaz.",
    "q.8.q": "VeltOS hangi dilleri konuşuyor?",
    "q.8.a": "VeltOS'un kendi uygulamaları Türkçe ve İngilizce konuşur; kurulum programı ve sistemin geri kalanı çok daha fazla dil sunar.",

    "foot.tag": "Senin Bilgisayarın. Sınır Tanıma.",
    "foot.releases": "Sürümler",
    "foot.issues": "Sorun bildir",
    "foot.dev": "Geliştirici belgeleri",
    "foot.by": "Geliştiren:",
    "foot.legal": "VeltOS özgür bir yazılımdır (GPL-3.0-or-later); Microsoft ile bağlantılı değildir ve Microsoft tarafından desteklenmez. Windows, Microsoft 365, Word, Excel, PowerPoint ve Copilot, Microsoft Corporation'ın ticari markalarıdır ve yalnızca VeltOS'un neye benzediğini anlatmak için anılır.",
    "lb.close": "Kapat"
  };
  var TITLES = {
    en: "VeltOS — Your PC. No Limits. | Free Windows 11-style Linux desktop",
    tr: "VeltOS — Senin Bilgisayarın. Sınır Tanıma. | Windows 11 tarzı ücretsiz işletim sistemi"
  };
  var DESCRIPTIONS = {
    tr: "VeltOS 1.0, Windows 11 gibi çalışan ücretsiz ve açık kaynaklı bir işletim sistemidir: Başlat, görev çubuğu, Dosya Gezgini, Ayarlar, Mağaza, VeltOS AI, Office, Windows programı desteği ve 20'den fazla kendi uygulaması. Debian 13 tabanlı. ISO'yu indirin."
  };
  var SITE = "https://veltos.ahmetfurkandemir.com/";

  var root = document.documentElement;
  root.classList.remove("no-js");
  root.classList.add("js-ready");
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function store(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* storage may be blocked */ }
  }

  /* Language ---------------------------------------------------------------- */
  var english = {};
  var textNodes = document.querySelectorAll("[data-i18n]");
  var attrNodes = document.querySelectorAll("[data-i18n-attr]");
  var description = document.querySelector('meta[name="description"]');
  var canonical = document.querySelector('link[rel="canonical"]');
  english.description = description ? description.getAttribute("content") : "";
  textNodes.forEach(function (el) { english[el.getAttribute("data-i18n")] = el.innerHTML; });
  attrNodes.forEach(function (el) {
    el.getAttribute("data-i18n-attr").split(";").forEach(function (pair) {
      var parts = pair.split(":");
      english["@" + parts[0] + ":" + parts[1]] = el.getAttribute(parts[0]) || "";
    });
  });

  function t(key) {
    return root.getAttribute("data-lang") === "tr" && TR[key] !== undefined ? TR[key] : english[key];
  }

  function formatCount(el, value) {
    var turkish = root.getAttribute("data-lang") === "tr";
    var text = value.toFixed(parseInt(el.getAttribute("data-decimals") || "0", 10));
    var suffix = (turkish && el.getAttribute("data-suffix-tr")) || el.getAttribute("data-suffix") || "";
    return (turkish ? text.replace(".", ",") : text) + suffix;
  }

  function applyLanguage(lang) {
    var turkish = lang === "tr";
    root.setAttribute("data-lang", lang);
    root.setAttribute("lang", lang);
    textNodes.forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      var value = turkish && TR[key] !== undefined ? TR[key] : english[key];
      if (value !== undefined && el.innerHTML !== value) el.innerHTML = value;
    });
    attrNodes.forEach(function (el) {
      el.getAttribute("data-i18n-attr").split(";").forEach(function (pair) {
        var parts = pair.split(":");
        var value = turkish && TR[parts[1]] !== undefined ? TR[parts[1]] : english["@" + parts[0] + ":" + parts[1]];
        if (value !== undefined) el.setAttribute(parts[0], value);
      });
    });
    document.title = TITLES[lang];
    if (description) description.setAttribute("content", turkish ? DESCRIPTIONS.tr : english.description);
    if (canonical) canonical.setAttribute("href", turkish ? SITE + "?lang=tr" : SITE);
    document.querySelectorAll("[data-count]").forEach(function (el) {
      if (el.dataset.done) el.textContent = formatCount(el, parseFloat(el.getAttribute("data-count")));
    });
  }

  applyLanguage(root.getAttribute("data-lang") === "tr" ? "tr" : "en");
  document.getElementById("lang-toggle").addEventListener("click", function () {
    var lang = root.getAttribute("data-lang") === "tr" ? "en" : "tr";
    applyLanguage(lang);
    store("veltos-lang", lang);
    // The address follows the language, so a shared link opens the same page.
    try {
      if (/^https?:/.test(location.protocol)) {
        history.replaceState(null, "", location.pathname + (lang === "tr" ? "?lang=tr" : "") + location.hash);
      }
    } catch (e) { /* not allowed for some pages */ }
  });

  /* Theme --------------------------------------------------------------------- */
  document.getElementById("theme-toggle").addEventListener("click", function () {
    var theme = root.getAttribute("data-theme") === "light" ? "dark" : "light";
    root.setAttribute("data-theme", theme);
    document.querySelector('meta[name="theme-color"]').setAttribute("content", theme === "light" ? "#f4f6fc" : "#060a1c");
    store("veltos-theme", theme);
  });

  /* Menu (small screens) ------------------------------------------------------ */
  var menu = document.getElementById("menu-toggle");
  var links = document.getElementById("nav-links");
  function closeMenu() {
    links.classList.remove("open");
    menu.setAttribute("aria-expanded", "false");
  }
  menu.addEventListener("click", function () {
    var open = links.classList.toggle("open");
    menu.setAttribute("aria-expanded", open ? "true" : "false");
  });
  links.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", closeMenu); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeMenu(); });

  /* The logo goes back to the top ("#top" is the top of the document while
     no element has that id). */
  document.querySelectorAll('a[href="#top"]').forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      closeMenu();
      window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
      try {
        if (location.hash) history.replaceState(null, "", location.pathname + location.search);
      } catch (err) { /* not allowed for some file:// pages */ }
    });
  });

  /* Header shadow, at most once per frame. */
  var nav = document.querySelector(".nav");
  var queued = false;
  function updateShadow() {
    queued = false;
    nav.classList.toggle("scrolled", window.scrollY > 8);
  }
  window.addEventListener("scroll", function () {
    if (!queued) { queued = true; requestAnimationFrame(updateShadow); }
  }, { passive: true });
  updateShadow();

  /* The current section in the menu, and the hero's animations resting while
     it is scrolled away (IntersectionObserver: nothing measured on scroll). */
  if ("IntersectionObserver" in window) {
    var menuLinks = Array.prototype.slice.call(links.querySelectorAll("a"));
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var id = entry.target.id;
        menuLinks.forEach(function (a) {
          a.classList.toggle("active", id !== "" && a.getAttribute("href") === "#" + id);
        });
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    document.querySelectorAll("main > section[id]").forEach(function (s) { spy.observe(s); });
    var hero = document.querySelector(".hero");
    if (hero) {
      new IntersectionObserver(function (entries) {
        root.classList.toggle("hero-away", !entries[0].isIntersecting);
      }).observe(hero);
    }
  }

  /* Download: every [data-iso-link] follows <meta name="veltos-iso-url">. */
  var isoMeta = document.querySelector('meta[name="veltos-iso-url"]');
  var isoUrl = isoMeta ? isoMeta.getAttribute("content") : "";
  if (/^https:\/\/\S+$/.test(isoUrl)) {
    document.querySelectorAll("[data-iso-link]").forEach(function (a) {
      a.setAttribute("href", isoUrl);
      a.setAttribute("rel", "noopener");
    });
  }

  /* Appear on scroll, count up ------------------------------------------------ */
  function countUp(el) {
    var target = parseFloat(el.getAttribute("data-count"));
    if (reduced) { el.textContent = formatCount(el, target); return; }
    var start = null;
    function frame(now) {
      if (start === null) start = now;
      var p = Math.min(1, (now - start) / 1400);
      el.textContent = formatCount(el, target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
  function appear(el) {
    el.classList.add("visible");
    var num = el.querySelector("[data-count]");
    if (num && !num.dataset.done) { num.dataset.done = "1"; countUp(num); }
  }
  var revealed = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        appear(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    var firstScreen = [];
    revealed.forEach(function (el, i) {
      el.style.transitionDelay = Math.min(i % 6, 5) * 60 + "ms";
      var box = el.getBoundingClientRect();
      if (box.top < window.innerHeight && box.bottom > 0) firstScreen.push(el);
      else observer.observe(el);
    });
    // At once, not in the next frame: a page opened in a background tab gets
    // no frames, and its first screen stayed empty. getBoundingClientRect has
    // applied the hidden style already, so the change still animates.
    firstScreen.forEach(appear);
  } else {
    revealed.forEach(function (el) { el.classList.add("visible"); });
    document.querySelectorAll("[data-count]").forEach(countUp);
  }

  /* The hero picture tilts towards the pointer. */
  var visual = document.getElementById("hero-visual");
  var tilt = visual && visual.querySelector(".tilt");
  if (tilt && !reduced && window.matchMedia("(pointer: fine)").matches) {
    visual.addEventListener("mousemove", function (e) {
      var r = visual.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width - 0.5;
      var y = (e.clientY - r.top) / r.height - 0.5;
      tilt.style.transform = "rotateY(" + (x * 12 - 4) + "deg) rotateX(" + (-y * 9 + 3) + "deg)";
    });
    visual.addEventListener("mouseleave", function () { tilt.style.transform = ""; });
  }

  /* Cards light up under the pointer. */
  document.querySelectorAll(".card").forEach(function (card) {
    card.addEventListener("mousemove", function (e) {
      var r = card.getBoundingClientRect();
      card.style.setProperty("--mx", (e.clientX - r.left) + "px");
      card.style.setProperty("--my", (e.clientY - r.top) + "px");
    });
  });

  /* Screenshot gallery ------------------------------------------------------- */
  var track = document.getElementById("showcase-track");
  var tabs = document.querySelectorAll(".tabs [data-shot]");
  var shots = track ? track.querySelectorAll(".shot") : [];
  function select(index) {
    tabs.forEach(function (tab, i) { tab.setAttribute("aria-selected", i === index ? "true" : "false"); });
  }
  function show(index) {
    if (!track) return;
    index = (index + shots.length) % shots.length;
    track.scrollTo({ left: shots[index].offsetLeft - track.offsetLeft, behavior: reduced ? "auto" : "smooth" });
    select(index);
  }
  function current() {
    return track ? Math.round(track.scrollLeft / track.clientWidth) : 0;
  }
  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () { show(parseInt(tab.getAttribute("data-shot"), 10)); });
  });
  if (track) {
    document.getElementById("shot-prev").addEventListener("click", function () { show(current() - 1); });
    document.getElementById("shot-next").addEventListener("click", function () { show(current() + 1); });
    var settle;
    track.addEventListener("scroll", function () {
      clearTimeout(settle);
      settle = setTimeout(function () { select(current()); }, 80);
    }, { passive: true });
  }

  /* Lightbox: shows the picture of the current theme. ------------------------ */
  var box = document.getElementById("lightbox");
  var boxImg = document.getElementById("lightbox-img");
  var opener = null;
  function closeBox() {
    box.hidden = true;
    document.body.style.overflow = "";
    if (opener) opener.focus();
  }
  document.querySelectorAll(".zoom").forEach(function (button) {
    button.addEventListener("click", function () {
      var visible = Array.prototype.filter.call(button.querySelectorAll("img"), function (img) {
        return img.offsetParent !== null || getComputedStyle(img).display !== "none";
      })[0];
      if (!visible) return;
      opener = button;
      boxImg.src = visible.currentSrc || visible.src;
      boxImg.alt = visible.alt;
      box.hidden = false;
      document.body.style.overflow = "hidden";
      document.getElementById("lightbox-close").focus();
    });
  });
  box.addEventListener("click", function (e) { if (e.target !== boxImg) closeBox(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !box.hidden) closeBox(); });

  /* Copy the ISO's checksum. */
  var copy = document.getElementById("copy-hash");
  if (copy) {
    copy.addEventListener("click", function () {
      var text = document.getElementById("iso-hash").textContent.trim();
      function done() {
        copy.textContent = t("d.copied") || "Copied";
        setTimeout(function () { copy.textContent = t("d.copy"); }, 1600);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      } else {
        var range = document.createRange();
        range.selectNodeContents(document.getElementById("iso-hash"));
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        try { document.execCommand("copy"); done(); } catch (e) { /* the text stays selected */ }
      }
    });
  }
})();
