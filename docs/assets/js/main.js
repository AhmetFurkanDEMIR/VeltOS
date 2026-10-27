/* VeltOS website: language (English / Turkish), light/dark theme, menu,
   scroll animations, counters, screenshot gallery and lightbox.
   Plain script, no modules or fetch: index.html also works when it is
   opened straight from disk. English is the page's own text; Turkish
   comes from TR below (a missing key keeps the English text). */
(function () {
  "use strict";

  var TR = {
    "skip": "İçeriğe geç",
    "aria.main": "Ana menü",
    "nav.features": "Özellikler",
    "nav.apps": "Uygulamalar",
    "nav.gallery": "Ekran görüntüleri",
    "nav.windows": "Windows programları",
    "nav.specs": "Teknik bilgiler",
    "nav.faq": "SSS",
    "nav.download": "İndir",
    "theme.toggle": "Açık veya koyu tema",
    "nav.menu": "Menü",
    "hero.eyebrow": "Sürüm 1.0 · Debian 13 tabanlı",
    "hero.title1": "Senin Bilgisayarın.",
    "hero.title2": "Sınır Tanıma.",
    "hero.lead": "VeltOS, Windows 11 kullanıcılarının alıştığı gibi çalışan bir masaüstü işletim sistemidir: Başlat menüsü, görev çubuğu, Dosya Gezgini, Ayarlar ve uygulama mağazası tam beklediğiniz yerde. Kendi uygulamaları, modern kurulum programı ve Wine ile Windows programı desteğiyle gelir. Ücretsizdir, açık kaynaktır ve Debian üzerine kuruludur.",
    "hero.get": "VeltOS'u indirin",
    "hero.source": "Kaynak kodu",
    "aria.highlights": "Öne çıkanlar",
    "hero.langs": "Türkçe · English",
    "img.desktop": "Başlat menüsü açıkken VeltOS masaüstü",
    "float.explorer": "Dosya Gezgini",
    "float.explorer.sub": "Sekmeler, Giriş, Bu bilgisayar",
    "float.store": "VeltOS Mağaza",
    "float.store.sub": "İmzalı, ücretsiz uygulamalar",
    "float.ready": "Yaklaşık 3 saniyede hazır",
    "float.ready.sub": "oturum açılışından masaüstüne*",
    "aria.numbers": "Rakamlarla VeltOS",
    "stats.packages": "VeltOS paketi ve uygulaması",
    "stats.tests": "her derlemede çalışan otomatik test",
    "stats.boot": "sistem açılışı*",
    "stats.signin": "oturum açılışından masaüstüne*",
    "stats.note": "* QEMU/KVM sanal makinesine kurulu bir sistemde ölçülmüştür (4 çekirdek, 3D hızlandırma yok). Açılış süresi, systemd-analyze'ın bildirdiği çekirdek ve kullanıcı alanı süresidir; üretici yazılımı ile önyükleme menüsü buna dahil değildir. Sonuçlar donanımınıza göre değişir.",
    "features.kicker": "İlk dakikadan tanıdık",
    "features.title": "Her şey beklediğiniz yerde",
    "features.lead": "Yeni alışkanlıklar edinmenize gerek yok. VeltOS, Windows 11'in düzenini ve küçük ayrıntılarını izlerken Linux'un hızını, güvenliğini ve özgürlüğünü korur.",
    "f.start.t": "Başlat, görev çubuğu, arama",
    "f.start.d": "Pencereleri canlı önizleyen ortalanmış görev çubuğu, sabitlenmiş uygulamaları ve önerileriyle Başlat menüsü, siz yazarken sonuç veren arama, sanal masaüstleriyle Görev Görünümü ve alıştığınız sağ tık menüleri.",
    "f.files.t": "Dosya Gezgini",
    "f.files.d": "Sekmeler, Giriş, Bu bilgisayar, Geri Dönüşüm Kutusu, Özellikler penceresi, zip dosyaları ve Windows sürücüleri. Üstelik her programda aynı dosya açma ve kaydetme pencereleri karşınıza çıkar.",
    "f.settings.t": "Tek bir Ayarlar uygulaması",
    "f.settings.d": "Wi-Fi, Bluetooth, ekran, ses, hesaplar, uygulamalar, gizlilik ve güncelleştirmeler; hepsi alıştığınız sayfalarda ve kendi dilinizde.",
    "f.store.t": "VeltOS Mağaza",
    "f.store.d": "Debian'ın imzalı arşivinden binlerce ücretsiz uygulama ve oyun, tek tıkla kurulur ve güncellenir.",
    "f.office.t": "Office ve e-posta",
    "f.office.d": "LibreOffice üzerinde Word, Excel ve PowerPoint başlangıç ekranları; belgeler varsayılan olarak Microsoft biçimlerinde kaydedilir. E-postalarınız içinse Outlook görünümünde VeltOS Mail var.",
    "f.windows.t": "Windows programları",
    "f.windows.d": "Bir .exe ya da .msi dosyasına çift tıklayın; VeltOS programı Wine ile kurar, Başlat'a ve Ayarlar'a ekler. Her program çalışmaz; çalışmadığında VeltOS bunu size bildirir.",
    "f.repair.t": "Otomatik Onarım",
    "f.repair.d": "VeltOS üst üste iki kez açılamazsa onarım ekranı kendiliğinden gelir: Başlangıç Onarımı, Güvenli mod, Komut İstemi ve nelerin ters gittiğine dair ayrıntılar.",
    "f.secure.t": "Varsayılan olarak güvenli",
    "f.secure.d": "Yazılımlar yalnızca imzalı Debian arşivlerinden gelir ya da VeltOS'un kendi kaynaklarından derlenir. Güvenli Önyükleme, AppArmor ve BitLocker gibi açılışta parola soran disk şifreleme de hazır gelir.",
    "f.style.t": "Size özel görünüm",
    "f.style.d": "Açık ve koyu mod, her biri kendi duvar kâğıdıyla gelen sekiz tema, tüm VeltOS uygulamalarına yansıyan bir vurgu rengi ve Windows 11'in animasyonları.",
    "apps.kicker": "VeltOS için geliştirildi",
    "apps.title": "Her gün kullandığınız uygulamalar",
    "apps.lead": "Hepsi VeltOS için, Windows 11'deki karşılıklarının düzeninde yazıldı; Türkçe ve İngilizce, açık ve koyu temada kullanılabilir.",
    "a.explorer": "Dosya Gezgini",
    "a.settings": "Ayarlar",
    "a.store": "VeltOS Mağaza",
    "a.mail": "VeltOS Mail",
    "a.calendar": "Takvim",
    "a.photos": "Fotoğraflar",
    "a.media": "Medya Oynatıcı",
    "a.camera": "Kamera",
    "a.snip": "Ekran Alıntısı Aracı",
    "a.calculator": "Hesap Makinesi",
    "a.notepad": "Not Defteri",
    "a.clock": "Saat",
    "a.pdf": "PDF Okuyucu",
    "a.archive": "Arşiv",
    "a.taskmanager": "Görev Yöneticisi",
    "a.disks": "Disk Yönetimi",
    "a.winapps": "Windows programları",
    "gallery.kicker": "Yakından bakın",
    "gallery.title": "VeltOS'tan ekran görüntüleri",
    "gallery.lead": "Görüntülerin hepsi VeltOS'un kendisinde alındı. Büyütmek için bir görüntüye tıklayın.",
    "aria.shots": "Ekran görüntüleri",
    "g.desktop": "Masaüstü",
    "g.explorer": "Dosya Gezgini",
    "g.settings": "Ayarlar",
    "g.store": "Mağaza",
    "g.office": "Office",
    "g.mail": "E-posta",
    "g.dark": "Koyu mod",
    "g.installer": "Kurulum",
    "g.repair": "Otomatik Onarım",
    "g.desktop.alt": "Masaüstü ve Başlat menüsü",
    "g.desktop.cap": "Başlat menüsü açık masaüstü: sabitlenmiş uygulamalar, öneriler ve görev çubuğundaki arama kutusu.",
    "g.explorer.cap": "Dosya Gezgini: sekmeler, gezinti bölmesi ve Office belgeleriniz.",
    "g.settings.cap": "Ayarlar: bütün sayfalar tek uygulamada; KDE'nin ayar penceresi hiç açılmaz.",
    "g.store.cap": "VeltOS Mağaza: Debian'ın imzalı arşivinden uygulamalar ve oyunlar.",
    "g.office.cap": "Word'ün başlangıç ekranı: şablonlardan yeni belgeler ve son açtığınız dosyalar.",
    "g.mail.cap": "Outlook görünümünde VeltOS Mail.",
    "g.dark.cap": "Nebula temasıyla koyu mod: mor vurgu rengi, koyu Başlat menüsü ve görev çubuğu.",
    "g.installer.cap": "Windows 11 kurulumunu andıran sayfalarıyla kurulum programı.",
    "g.repair.cap": "Yarım kalan iki açılışın ardından gelen Otomatik Onarım ekranı.",
    "g.prev": "Önceki",
    "g.next": "Sonraki",
    "w.kicker": "Windows programları",
    "w.title": "Çift tıklayın. Kurun. Başlat'ta bulun.",
    "w.lead": "VeltOS, Windows kurulum dosyalarını ve programlarını Wine ile tek bir Windows ortamında açar; tıpkı bir bilgisayardaki tek C: sürücüsü gibi. Kurduğunuz programlar Başlat'ta ve Ayarlar'da görünür; onları Windows'ta olduğu gibi Ayarlar'dan kaldırabilirsiniz.",
    "w.s1.t": ".exe ya da .msi dosyasını açın",
    "w.s1.d": "VeltOS dosyanın adını, yayımcısını ve simgesini okur, ardından ne yapacağını gösterir.",
    "w.s2.t": "Kurun",
    "w.s2.d": "Programın kendi kurulum sihirbazı çalışır. Wine Mono ve Gecko hazır geldiği için internetten hiçbir şey indirilmez.",
    "w.s3.t": "Diğer uygulamalar gibi kullanın",
    "w.s3.d": "Program Başlat'ta yer alır ve Ayarlar › Uygulamalar'da listelenir. Vulkan destekleyen ekran kartlarında oyunlar için DXVK kullanılır.",
    "w.honest": "Açık konuşalım: Wine her Windows programını çalıştıramaz ve bir güvenlik yalıtımı (sandbox) değildir. Yalnızca güvendiğiniz programları çalıştırın.",
    "w.window": "Windows programı kur",
    "w.publisher": "Igor Pavlov · 64 bit",
    "w.progress": "Kuruluyor… Program Başlat'ta görünecek.",
    "d.kicker": "İndir",
    "d.title": "VeltOS 1.0'ı indirin",
    "d.lead": "64 bit bilgisayarlar için hazırlanan tek bir ISO dosyası hem canlı sistem olarak açılır hem de VeltOS'u kurar. Önce canlı olarak deneyin, sonra Windows'un yanına ya da yerine kurun.",
    "dl.badge": "ilk sürüm",
    "dl.meta.arch": "64 bit bilgisayarlar (amd64)",
    "dl.meta.size": "ISO · 2,45 GB",
    "dl.meta.fw": "UEFI · BIOS · Güvenli Önyükleme",
    "dl.meta.base": "Debian 13 tabanlı",
    "dl.button": "ISO'yu indir",
    "dl.soon": "Yakında",
    "dl.pending": "İndirme bağlantısı çok yakında burada olacak. O zamana kadar aynı ISO'yu kaynak kodundan kendiniz derleyebilirsiniz (aşağıya bakın).",
    "d.copy": "Kopyala",
    "dl.s1.t": "İndirin",
    "dl.s1.d": "Yaklaşık 2,45 GB'lık tek bir ISO dosyası. İndirdikten sonra SHA-256 değerini yukarıdakiyle karşılaştırın.",
    "dl.s2.t": "Başlatın",
    "dl.s2.d": "ISO'yu bir USB belleğe yazın ve bilgisayarınızı ondan başlatın (ya da bir sanal makinede açın). VeltOS canlı sistem olarak açılır; kurmadan önce göz atabilirsiniz.",
    "dl.s3.t": "Deneyin ya da kurun",
    "dl.s3.d": "VeltOS'u bilgisayarınızda hiçbir şeyi değiştirmeden deneyin; hazır olduğunuzda masaüstünden kurun.",
    "d.build.t": "ISO'yu derleyin",
    "d.build.d": "Her şey Docker içinde derlenir ve test edilir; bilgisayarınızda yalnızca Docker ve bash gerekir.",
    "r.title": "Minimum sistem gereksinimleri",
    "r.cpu": "İşlemci",
    "r.cpu.v": "64 bit x86 (amd64)",
    "r.ram": "Bellek",
    "r.disk": "Depolama",
    "r.fw": "Üretici yazılımı",
    "r.fw.v": "UEFI (Güvenli Önyükleme desteklenir) veya BIOS",
    "r.gpu": "Ekran kartı",
    "r.gpu.v": "Herhangi biri; 3D hızlandırma yoksa görüntü yazılımla oluşturulur",
    "r.note": "Sanal makinelerde (QEMU/KVM, VirtualBox) test edildi ve gerçek bir bilgisayara (NVIDIA ekran kartlı bir dizüstü) kuruldu.",
    "s.kicker": "Perde arkası",
    "s.title": "Sürüm 1.0: kendini kanıtlamış yazılımlar üzerine kurulu",
    "s.lead": "VeltOS, olgun açık kaynak yazılımları çatallamadan (fork etmeden) olduğu gibi kullanır ve bunların üzerine küçük, test edilmiş kendi paketlerini ekler.",
    "s.version": "Sürüm",
    "s.version.v": "1.0",
    "s.base": "Temel sistem",
    "s.kernel": "Çekirdek",
    "s.desktop": "Masaüstü",
    "s.desktop.v": "Wayland üzerinde KDE Plasma 6.3; görev çubuğu, Başlat menüsü ve Görev Görünümü VeltOS'a ait",
    "s.installer": "Kurulum programı",
    "s.installer.v": "VeltOS'a özel sayfalarla Calamares 3.3; isteğe bağlı disk şifreleme",
    "s.office": "Ofis",
    "s.browser": "Web ve e-posta",
    "s.windows": "Windows programları",
    "s.apps": "VeltOS uygulamaları",
    "s.apps.v": "Python ve Qt Quick (PySide6 6.8)",
    "s.langs": "Diller",
    "s.langs.v": "Türkçe, İngilizce",
    "s.iso": "ISO",
    "s.iso.v": "USB bellek ve DVD için tek bir hibrit kalıp; canlı sistem ve kurulum bir arada",
    "s.license": "Lisans",
    "s.license.v": "Özgür ve açık kaynak (GPL ve uyumlu lisanslar; görseller CC BY-SA 4.0)",
    "s.quality.t": "Her derlemede test edilir",
    "s.quality.d": "Her paket derlenirken kendi birim testlerini çalıştırır; sistem kalıbı da yazılmadan önce kendini denetler. Ardından her ISO, QEMU'da UEFI ve BIOS ile açılır; masaüstü, çökmeler ve açılış süreleri tek tek kontrol edilir.",
    "s.light.t": "Tasarımı gereği hafif",
    "s.light.d": "Her arka plan hizmeti yerini hak etmek zorunda; açılış süresi ve bellek kullanımı her ISO'da yeniden ölçülür.",
    "q.kicker": "Sorular",
    "q.title": "Sıkça sorulan sorular",
    "q.1.q": "VeltOS bir Windows sürümü mü?",
    "q.1.a": "Hayır. VeltOS, Debian üzerine kurulu bir Linux dağıtımıdır. Kendinizi evinizde hissetmeniz için Windows 11 gibi görünür ve davranır, ancak ayrı bir işletim sistemidir ve Microsoft ile hiçbir bağlantısı yoktur.",
    "q.2.q": "Windows programlarım çalışır mı?",
    "q.2.a": "Birçoğu Wine sayesinde çalışır; bazıları hiç çalışmaz, bazıları ise sorunlu çalışır. VeltOS her programın çalışacağı sözünü vermez; ne olduğunu size açıkça gösterir ve pek çok iş için kendi uygulamalarını sunar.",
    "q.3.q": "Ücretli mi?",
    "q.3.a": "Hayır. VeltOS ücretsiz ve açık kaynaktır; üzerine kurulduğu yazılımlar da öyle.",
    "q.4.q": "Günlük kullanıma hazır mı?",
    "q.4.a": "VeltOS 1.0, herkese açık ilk sürümdür. Her yeni sistemde olduğu gibi kurmadan önce dosyalarınızı yedekleyin ve çalışmayan bir şey görürseniz GitHub üzerinden bize bildirin.",
    "q.7.q": "VeltOS'u sanal makinede deneyebilir miyim?",
    "q.7.a": "Evet, VeltOS zaten sanal makinelerde test ediliyor. Sanal makineye 4 GB bellek ve 25 GB disk ayırın; UEFI de BIOS da çalışır. 3D hızlandırmayı açarsanız masaüstü daha akıcı olur. Hyper-V'nin açık olduğu Windows bilgisayarlarda (WSL2, Docker Desktop) VirtualBox, sanal makineyi bir tuşa basılana kadar dondurabilir; bu, VirtualBox'ın bilinen bir hatasıdır. QEMU/KVM bu sorundan etkilenmez.",
    "q.5.q": "Güncelleştirmeler nereden gelir?",
    "q.5.a": "Güncelleştirmeler Debian'ın imzalı arşivlerinden gelir ve VeltOS Mağaza ile Ayarlar üzerinden kurulur. VeltOS'un kendi paketleri ise GitHub'daki kaynak kodundan derlenir.",
    "q.6.q": "Hangi dilleri destekliyor?",
    "q.6.a": "VeltOS'un kendi pencerelerinin tamamı Türkçe ve İngilizcedir. Debian ve KDE'den gelen bileşenler çok daha fazla dilde kullanılabilir.",
    "foot.tag": "Senin Bilgisayarın. Sınır Tanıma.",
    "aria.footer": "Alt bilgi",
    "foot.source": "Kaynak kodu",
    "foot.status": "Proje durumu",
    "foot.issues": "Sorun bildirin",
    "foot.legal": "VeltOS; Debian, KDE Plasma, LibreOffice, Firefox, Wine ve Calamares üzerine kurulu bağımsız bir projedir. Microsoft ile bağlantılı değildir ve Microsoft tarafından desteklenmez. Windows, Word, Excel, PowerPoint ve Outlook, Microsoft Corporation'ın ticari markalarıdır; burada yalnızca VeltOS'un neye benzediğini anlatmak için anılır. VeltOS görselleri © VeltOS Geliştiricileri, CC BY-SA 4.0.",
    "aria.shot": "Ekran görüntüsü",
    "lb.close": "Kapat",
    "d.copied": "Kopyalandı"
  };
  var TITLES = {
    en: "VeltOS — Your PC. No Limits.",
    tr: "VeltOS — Senin Bilgisayarın. Sınır Tanıma."
  };

  var root = document.documentElement;
  root.classList.remove("no-js");

  function store(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* storage may be blocked on file:// */ }
  }

  /* Language */
  var english = {};
  var textNodes = document.querySelectorAll("[data-i18n]");
  var attrNodes = document.querySelectorAll("[data-i18n-attr]");
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

  function applyLanguage(lang) {
    root.setAttribute("data-lang", lang);
    root.setAttribute("lang", lang);
    textNodes.forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      var value = lang === "tr" && TR[key] !== undefined ? TR[key] : english[key];
      if (value !== undefined && el.innerHTML !== value) el.innerHTML = value;
    });
    attrNodes.forEach(function (el) {
      el.getAttribute("data-i18n-attr").split(";").forEach(function (pair) {
        var parts = pair.split(":");
        var value = lang === "tr" && TR[parts[1]] !== undefined ? TR[parts[1]] : english["@" + parts[0] + ":" + parts[1]];
        if (value !== undefined) el.setAttribute(parts[0], value);
      });
    });
    document.title = TITLES[lang];
    document.querySelectorAll("[data-count]").forEach(function (el) {
      if (el.dataset.done) el.textContent = formatCount(el, parseFloat(el.getAttribute("data-count")));
    });
  }

  /* Numbers in the page's language: "4.0 s" in English, "4,0 sn" in Turkish. */
  function formatCount(el, value) {
    var turkish = root.getAttribute("data-lang") === "tr";
    var text = value.toFixed(parseInt(el.getAttribute("data-decimals") || "0", 10));
    var suffix = (turkish && el.getAttribute("data-suffix-tr")) || el.getAttribute("data-suffix") || "";
    return (turkish ? text.replace(".", ",") : text) + suffix;
  }

  applyLanguage(root.getAttribute("data-lang") === "tr" ? "tr" : "en");
  document.getElementById("lang-toggle").addEventListener("click", function () {
    var lang = root.getAttribute("data-lang") === "tr" ? "en" : "tr";
    applyLanguage(lang);
    store("veltos-lang", lang);
  });

  /* Theme */
  document.getElementById("theme-toggle").addEventListener("click", function () {
    var theme = root.getAttribute("data-theme") === "light" ? "dark" : "light";
    root.setAttribute("data-theme", theme);
    document.querySelector('meta[name="theme-color"]').setAttribute("content", theme === "light" ? "#f5f7fd" : "#050818");
    store("veltos-theme", theme);
  });

  /* Menu (small screens) */
  var menu = document.getElementById("menu-toggle");
  var links = document.getElementById("nav-links");
  menu.addEventListener("click", function () {
    var open = links.classList.toggle("open");
    menu.setAttribute("aria-expanded", open ? "true" : "false");
  });
  links.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", function () {
      links.classList.remove("open");
      menu.setAttribute("aria-expanded", "false");
    });
  });

  /* The logo goes back to the top of the page ("#top" is the top of the
     document in HTML; this also scrolls smoothly and keeps "#top" out of
     the address). */
  document.querySelectorAll('a[href="#top"]').forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      links.classList.remove("open");
      menu.setAttribute("aria-expanded", "false");
      window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
      try {
        if (location.hash) history.replaceState(null, "", location.pathname + location.search);
      } catch (err) { /* not allowed for some file:// pages */ }
    });
  });

  /* Header shadow, at most once per frame */
  var nav = document.querySelector(".nav");
  var shadowQueued = false;
  function updateShadow() {
    shadowQueued = false;
    nav.classList.toggle("scrolled", window.scrollY > 8);
  }
  window.addEventListener("scroll", function () {
    if (!shadowQueued) { shadowQueued = true; requestAnimationFrame(updateShadow); }
  }, { passive: true });
  updateShadow();

  /* The current section in the menu, and the hero's animations resting while
     it is scrolled away; IntersectionObservers, so nothing is measured while
     the page scrolls. */
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
    document.querySelectorAll("main > section").forEach(function (s) { spy.observe(s); });
    var hero = document.querySelector(".hero");
    if (hero) {
      new IntersectionObserver(function (entries) {
        root.classList.toggle("hero-away", !entries[0].isIntersecting);
      }).observe(hero);
    }
  }

  /* Download: every [data-iso-link] follows <meta name="veltos-iso-url">;
     until the ISO is published the download button waits (the head script
     marks the page iso-pending). */
  var isoMeta = document.querySelector('meta[name="veltos-iso-url"]');
  var isoUrl = isoMeta ? isoMeta.getAttribute("content") : "";
  var isoReady = /^https:\/\/\S+$/.test(isoUrl);
  document.querySelectorAll("[data-iso-link]").forEach(function (a) {
    if (isoReady) {
      a.setAttribute("href", isoUrl);
      a.setAttribute("rel", "noopener");
    } else if (a.classList.contains("dl-button")) {
      a.setAttribute("aria-disabled", "true");
      a.setAttribute("tabindex", "-1");
    }
  });

  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Appear on scroll, count up */
  function countUp(el) {
    var target = parseFloat(el.getAttribute("data-count"));
    if (reduced) { el.textContent = formatCount(el, target); return; }
    var start = null;
    function frame(now) {
      if (start === null) start = now;
      var p = Math.min(1, (now - start) / 1400);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = formatCount(el, target * eased);
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
  var revealed = document.querySelectorAll(".reveal");
  function appear(el) {
    el.classList.add("visible");
    var num = el.querySelector("[data-count]");
    if (num && !num.dataset.done) { num.dataset.done = "1"; countUp(num); }
  }
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
      // What is on the first screen appears at once, without waiting for
      // the observer's first callback (getBoundingClientRect has already
      // applied the hidden style, so the change still animates).
      if (box.top < window.innerHeight && box.bottom > 0) firstScreen.push(el);
      else observer.observe(el);
    });
    firstScreen.forEach(appear);
  } else {
    revealed.forEach(function (el) { el.classList.add("visible"); });
    document.querySelectorAll("[data-count]").forEach(countUp);
  }

  /* The hero picture tilts towards the pointer */
  var visual = document.getElementById("hero-visual");
  var screen = visual && visual.querySelector(".tilt");
  if (screen && !reduced && window.matchMedia("(pointer: fine)").matches) {
    visual.addEventListener("mousemove", function (e) {
      var r = visual.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width - 0.5;
      var y = (e.clientY - r.top) / r.height - 0.5;
      screen.style.transform = "rotateY(" + (x * 14 - 4) + "deg) rotateX(" + (-y * 10 + 3) + "deg)";
    });
    visual.addEventListener("mouseleave", function () { screen.style.transform = ""; });
  }

  /* Cards light up under the pointer */
  document.querySelectorAll(".card").forEach(function (card) {
    card.addEventListener("mousemove", function (e) {
      var r = card.getBoundingClientRect();
      card.style.setProperty("--mx", (e.clientX - r.left) + "px");
      card.style.setProperty("--my", (e.clientY - r.top) + "px");
    });
  });

  /* Screenshot gallery */
  var track = document.getElementById("showcase-track");
  var tabs = document.querySelectorAll(".tabs [data-shot]");
  var shots = track ? track.querySelectorAll(".shot") : [];
  function show(index) {
    if (!track) return;
    index = (index + shots.length) % shots.length;
    track.scrollTo({ left: shots[index].offsetLeft - track.offsetLeft, behavior: reduced ? "auto" : "smooth" });
    select(index);
  }
  function select(index) {
    tabs.forEach(function (tab, i) { tab.setAttribute("aria-selected", i === index ? "true" : "false"); });
  }
  function currentShot() {
    return track ? Math.round(track.scrollLeft / track.clientWidth) : 0;
  }
  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () { show(parseInt(tab.getAttribute("data-shot"), 10)); });
  });
  if (track) {
    document.getElementById("shot-prev").addEventListener("click", function () { show(currentShot() - 1); });
    document.getElementById("shot-next").addEventListener("click", function () { show(currentShot() + 1); });
    var settle;
    track.addEventListener("scroll", function () {
      clearTimeout(settle);
      settle = setTimeout(function () { select(currentShot()); }, 80);
    }, { passive: true });
  }

  /* Lightbox */
  var box = document.getElementById("lightbox");
  var boxImg = document.getElementById("lightbox-img");
  function closeBox() { box.hidden = true; document.body.style.overflow = ""; }
  document.querySelectorAll(".zoom").forEach(function (button) {
    button.addEventListener("click", function () {
      var img = button.querySelector("img");
      boxImg.src = button.getAttribute("data-full");
      boxImg.alt = img ? img.alt : "";
      box.hidden = false;
      document.body.style.overflow = "hidden";
      document.getElementById("lightbox-close").focus();
    });
  });
  document.getElementById("lightbox-close").addEventListener("click", closeBox);
  box.addEventListener("click", function (e) { if (e.target === box) closeBox(); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !box.hidden) closeBox();
    if (box.hidden && document.activeElement && document.activeElement.closest && document.activeElement.closest(".showcase")) {
      if (e.key === "ArrowRight") show(currentShot() + 1);
      if (e.key === "ArrowLeft") show(currentShot() - 1);
    }
  });

  /* Copy the build commands */
  document.querySelectorAll("[data-copy]").forEach(function (button) {
    button.addEventListener("click", function () {
      var text = document.getElementById(button.getAttribute("data-copy")).textContent;
      function done() {
        button.textContent = t("d.copied") || "Copied";
        button.classList.add("done");
        setTimeout(function () { button.textContent = t("d.copy"); button.classList.remove("done"); }, 1600);
      }
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, function () {});
      } else {
        var area = document.createElement("textarea");
        area.value = text;
        document.body.appendChild(area);
        area.select();
        try { document.execCommand("copy"); done(); } catch (e) {}
        document.body.removeChild(area);
      }
    });
  });

  document.getElementById("year").textContent = String(new Date().getFullYear());
})();
