/* VeltOS website: language (English / Turkish), light/dark theme, menu,
   scroll animations, counters, screenshot gallery and lightbox.
   Plain script, no modules or fetch: index.html also works when it is
   opened straight from disk. English is the page's own text; Turkish
   comes from TR below (a missing key keeps the English text). */
(function () {
  "use strict";

  var TR = {
    "skip": "İçeriğe geç",
    "nav.features": "Özellikler",
    "nav.apps": "Uygulamalar",
    "nav.gallery": "Ekran görüntüleri",
    "nav.windows": "Windows programları",
    "nav.specs": "Teknik bilgiler",
    "nav.faq": "SSS",
    "nav.download": "İndir",
    "nav.menu": "Menü",
    "theme.toggle": "Açık veya koyu tema",
    "hero.eyebrow": "Sürüm 0.1 · ön alfa · Debian 13 tabanlı",
    "hero.title1": "Bilgisayarınız.",
    "hero.title2": "Sınırsız.",
    "hero.lead": "VeltOS, Windows 11 kullanıcılarının zaten bildiği gibi çalışan bir masaüstü işletim sistemidir: Başlat, görev çubuğu, Dosya Gezgini, Ayarlar ve bir Mağaza; üstüne kendi uygulamaları, modern bir kurulum programı ve Wine ile Windows programı desteği. Ücretsiz, açık kaynak ve Debian üzerine kurulu.",
    "hero.get": "VeltOS'u indirin",
    "hero.source": "Kaynak kodu",
    "hero.langs": "Türkçe · English",
    "img.desktop": "Başlat menüsü açık VeltOS masaüstü",
    "float.explorer": "Dosya Gezgini",
    "float.explorer.sub": "Sekmeler, Giriş, Bu bilgisayar",
    "float.store": "VeltOS Mağaza",
    "float.store.sub": "İmzalı, ücretsiz uygulamalar",
    "float.ready": "Yaklaşık 3 saniyede hazır",
    "float.ready.sub": "oturum açmadan masaüstüne*",
    "stats.packages": "VeltOS paketi ve uygulaması",
    "stats.tests": "her derlemede otomatik test",
    "stats.boot": "sistem açılışı*",
    "stats.signin": "oturum açmadan masaüstüne*",
    "stats.note": "* Kurulu bir sistemde, QEMU/KVM sanal makinesinde ölçüldü (4 çekirdek, 3D hızlandırma yok). Açılış, systemd-analyze'ın bildirdiği çekirdek ve kullanıcı alanı süresidir; ürün yazılımı ve önyükleme menüsü dahil değildir. Sizin donanımınızda farklı olur.",
    "features.kicker": "İlk dakikadan tanıdık",
    "features.title": "Her şey beklediğiniz yerde",
    "features.lead": "Yeni alışkanlıklar edinmeniz gerekmez. VeltOS, Windows 11'in düzenini ve küçük ayrıntılarını izler; Linux'un hızını, güvenliğini ve özgürlüğünü korur.",
    "f.start.t": "Başlat, görev çubuğu, arama",
    "f.start.d": "Canlı pencere önizlemeli ortalanmış görev çubuğu, sabitlenmiş uygulamalar ve önerilerle Başlat, yazdıkça arama, sanal masaüstleriyle Görev Görünümü ve bildiğiniz sağ tık menüleri.",
    "f.files.t": "Dosya Gezgini",
    "f.files.d": "Sekmeler, Giriş, Bu bilgisayar, Geri Dönüşüm Kutusu, Özellikler, zip dosyaları ve Windows sürücüleri; her programda aynı dosya pencereleri.",
    "f.settings.t": "Tek bir Ayarlar uygulaması",
    "f.settings.d": "Wi-Fi, Bluetooth, ekran, ses, hesaplar, uygulamalar, gizlilik ve güncelleştirmeler zaten bildiğiniz sayfalarda, kendi dilinizde.",
    "f.store.t": "VeltOS Mağaza",
    "f.store.d": "Debian'ın imzalı arşivinden binlerce ücretsiz uygulama ve oyun; tek tıkla kurulur ve güncellenir.",
    "f.office.t": "Office ve Posta",
    "f.office.d": "LibreOffice üzerinde Word, Excel ve PowerPoint başlangıç ekranları, varsayılan olarak Microsoft biçimlerinde kayıt ve Outlook görünümünde VeltOS Mail.",
    "f.windows.t": "Windows programları",
    "f.windows.d": "Bir .exe veya .msi dosyasına çift tıklayın: VeltOS onu Wine ile kurar, Başlat'a ve Ayarlar'a ekler. Her program henüz çalışmıyor; VeltOS size söyler.",
    "f.repair.t": "Otomatik Onarım",
    "f.repair.d": "VeltOS üst üste iki kez açılamazsa bir onarım ekranı Başlangıç Onarımı, Güvenli mod, Komut İstemi ve son açılışın sorunlarını sunar.",
    "f.secure.t": "Varsayılan olarak güvenli",
    "f.secure.d": "Yazılım yalnızca imzalı Debian arşivlerinden ya da VeltOS'un kendi kaynaklarından gelir; Güvenli Önyükleme, AppArmor ve BitLocker gibi açılışta parola soran disk şifreleme.",
    "f.style.t": "Size ait görünüm",
    "f.style.d": "Açık ve koyu mod, kendi duvar kâğıtlarıyla sekiz tema, her VeltOS uygulamasına geçen bir vurgu rengi ve Windows 11'in animasyonları.",
    "apps.kicker": "VeltOS için yazıldı",
    "apps.title": "Her gün açtığınız uygulamalar",
    "apps.lead": "Windows 11'deki karşılıklarının düzeninde, Türkçe ve İngilizce, açık ve koyu temada VeltOS için yazıldı.",
    "a.explorer": "Dosya Gezgini",
    "a.settings": "Ayarlar",
    "a.store": "Mağaza",
    "a.mail": "Posta",
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
    "gallery.kicker": "Görün",
    "gallery.title": "VeltOS'tan ekran görüntüleri",
    "gallery.lead": "VeltOS'un kendisinde, bir sanal makinede çekildi. Büyütmek için resme tıklayın.",
    "g.desktop": "Masaüstü",
    "g.explorer": "Dosya Gezgini",
    "g.settings": "Ayarlar",
    "g.store": "Mağaza",
    "g.office": "Office",
    "g.mail": "Posta",
    "g.dark": "Koyu mod",
    "g.installer": "Kurulum",
    "g.repair": "Otomatik Onarım",
    "g.desktop.alt": "Masaüstü ve Başlat",
    "g.desktop.cap": "Başlat ile masaüstü: sabitlenmiş uygulamalar, öneriler ve görev çubuğundaki arama.",
    "g.explorer.cap": "Sekmeler, gezinti bölmesi ve Office dosyalarınızla Dosya Gezgini.",
    "g.settings.cap": "Ayarlar: her sayfa yerleşik, KDE'nin ayar penceresi hiç açılmaz.",
    "g.store.cap": "VeltOS Mağaza: Debian'ın imzalı arşivinden uygulamalar ve oyunlar.",
    "g.office.cap": "Word'ün başlangıç ekranı: şablonlardan yeni belgeler ve son dosyalarınız.",
    "g.mail.cap": "Outlook görünümünde VeltOS Mail.",
    "g.dark.cap": "Nebula temasıyla koyu mod: mor vurgu rengi, koyu Başlat ve görev çubuğu.",
    "g.installer.cap": "Windows 11 kurulumunun düzeninde kurulum programı.",
    "g.repair.cap": "İki yarım kalan açılıştan sonra Otomatik Onarım.",
    "g.prev": "Önceki",
    "g.next": "Sonraki",
    "w.kicker": "Windows programları",
    "w.title": "Çift tıklayın. Kurun. Başlat'ta bulun.",
    "w.lead": "VeltOS, Windows kurulum dosyalarını ve programlarını Wine ile tek bir Windows ortamında açar; bir bilgisayardaki tek C: sürücüsü gibi. Kurulan programlar Başlat'ta ve Ayarlar'da görünür ve Windows'taki gibi oradan kaldırılır.",
    "w.s1.t": ".exe veya .msi dosyasını açın",
    "w.s1.d": "VeltOS adını, yayımcısını ve simgesini okur ve ne yapacağını gösterir.",
    "w.s2.t": "Kurun",
    "w.s2.d": "Programın kendi kurulum programı çalışır; Wine Mono ve Gecko zaten yüklüdür, hiçbir şey indirilmez.",
    "w.s3.t": "Her uygulama gibi kullanın",
    "w.s3.d": "Başlat'ta yer alır, Ayarlar › Uygulamalar'da listelenir; Vulkan destekli ekran kartlarında oyunlar için DXVK.",
    "w.honest": "Dürüst not: Wine her Windows programını çalıştırmaz ve bir güvenlik korumalı alanı değildir; yalnızca güvendiğiniz programları çalıştırın.",
    "w.window": "Windows programı yükle",
    "w.publisher": "Igor Pavlov · 64 bit",
    "w.progress": "Yükleniyor… program Başlat'ta görünecek.",
    "d.kicker": "İndir",
    "d.title": "VeltOS 0.1'i edinin",
    "d.lead": "64 bit bilgisayarlar için tek bir ISO: canlı sistem olarak açılır ve VeltOS'u kurar. VeltOS ön alfa aşamasındadır: güvendiğiniz bilgisayarda değil, bir sanal makinede ya da yedek bir bilgisayarda deneyin.",
    "dl.badge": "ön alfa",
    "dl.meta.arch": "64 bit bilgisayarlar (amd64)",
    "dl.meta.size": "ISO · 2,45 GB",
    "dl.meta.base": "Debian 13 tabanlı",
    "dl.button": "ISO'yu indir",
    "dl.soon": "Yakında",
    "dl.pending": "İndirme bağlantısı yakında burada yayımlanacak. O zamana kadar aynı ISO'yu kaynak kodundan kendiniz derleyebilirsiniz (aşağıda).",
    "dl.s1.t": "İndirin",
    "dl.s1.d": "Yaklaşık 2,45 GB'lık tek bir ISO dosyası. SHA-256 değerini yukarıdakiyle karşılaştırın.",
    "dl.s2.t": "Başlatın",
    "dl.s2.d": "Bir sanal makinede ya da yedek bir bilgisayarda USB bellekten. VeltOS şimdiye kadar yalnızca sanal makinelerde test edildi.",
    "dl.s3.t": "Deneyin ya da kurun",
    "dl.s3.d": "VeltOS'u hiçbir şeyi değiştirmeden deneyin, hazır olduğunuzda masaüstünden kurun.",
    "d.build.t": "ISO'yu derleyin",
    "d.build.d": "Her şey Docker içinde derlenir ve test edilir; bilgisayarınıza başka bir şey gerekmez.",
    "d.copy": "Kopyala",
    "d.copied": "Kopyalandı",
    "d.vm.t": "Sanal makinede",
    "d.vm.1": "4 GB bellek ve 25 GB disk",
    "d.vm.2": "UEFI veya BIOS, 64 bit",
    "d.vm.3": "En akıcı masaüstü için 3D hızlandırmayı açın; kapalıyken VeltOS yazılımla çizer",
    "d.vm.4": "VirtualBox ve QEMU/KVM'de test edildi",
    "d.vm.5": "Hyper-V'nin açık olduğu bir Windows bilgisayarda (WSL2, Docker Desktop) VirtualBox, sanal makineleri bir tuşa basana ya da fareyi oynatana kadar dondurabiliyor; bu bilinen bir VirtualBox hatası. QEMU/KVM bundan etkilenmez",
    "r.title": "Sistem gereksinimleri",
    "r.cpu": "İşlemci",
    "r.cpu.v": "64 bit x86 (amd64)",
    "r.ram": "Bellek",
    "r.ram.v": "En az 2 GB, önerilen 4 GB",
    "r.disk": "Depolama",
    "r.disk.v": "En az 20 GB",
    "r.fw": "Ürün yazılımı",
    "r.fw.v": "UEFI (Güvenli Önyükleme destekli) veya BIOS",
    "r.gpu": "Ekran kartı",
    "r.gpu.v": "Herhangi biri; OpenGL donanımı önerilir",
    "s.kicker": "Kaputun altında",
    "s.title": "Sürüm 0.1, kanıtlanmış parçalar üzerinde",
    "s.lead": "VeltOS olgun açık kaynak yazılımları çatallamadan kullanır ve üzerine küçük, test edilmiş kendi paketlerini ekler.",
    "s.version": "Sürüm",
    "s.version.v": "0.1 (ön alfa)",
    "s.base": "Temel",
    "s.kernel": "Çekirdek",
    "s.desktop": "Masaüstü",
    "s.desktop.v": "Wayland üzerinde KDE Plasma 6.3; VeltOS'un görev çubuğu, Başlat'ı ve Görev Görünümü ile",
    "s.installer": "Kurulum",
    "s.installer.v": "VeltOS sayfalarıyla Calamares 3.3; isteğe bağlı disk şifreleme",
    "s.office": "Ofis",
    "s.browser": "Web ve posta",
    "s.windows": "Windows programları",
    "s.apps": "VeltOS uygulamaları",
    "s.apps.v": "Python ve Qt Quick (PySide6 6.8)",
    "s.langs": "Diller",
    "s.langs.v": "Türkçe, İngilizce",
    "s.iso": "ISO",
    "s.iso.v": "USB bellekler ve DVD'ler için tek bir hibrit kalıp; canlı sistem ve kurulum bir arada",
    "s.license": "Lisans",
    "s.license.v": "Özgür ve açık kaynak (GPL ve uyumlu lisanslar; görseller CC BY-SA 4.0)",
    "s.quality.t": "Her derlemede test edilir",
    "s.quality.d": "Her paket derlenirken birim testlerini çalıştırır, kalıp yazılmadan önce kendini denetler ve her ISO, masaüstü, çökmeler ve açılış süreleri denetlenerek QEMU'da UEFI ve BIOS ile açılır.",
    "s.light.t": "Tasarımı gereği hafif",
    "s.light.d": "Her arka plan hizmeti yerini hak etmelidir; açılış ve bellek kullanımı her ISO için ölçülür.",
    "q.kicker": "Sorular",
    "q.title": "Sık sorulanlar",
    "q.1.q": "VeltOS, Windows mu?",
    "q.1.a": "Hayır. VeltOS, Debian üzerine kurulu bir Linux sistemidir. Kendinizi evinizde hissetmeniz için Windows 11 gibi görünür ve davranır, ancak farklı bir işletim sistemidir ve Microsoft ile bağlantısı yoktur.",
    "q.2.q": "Windows programlarım çalışır mı?",
    "q.2.a": "Birçoğu Wine ile çalışır; bazıları çalışmaz, bazıları sorunlarla çalışır. VeltOS her programın çalışacağını asla vaat etmez; ne olduğunu size gösterir ve birçok iş için kendi uygulamalarını sunar.",
    "q.3.q": "Ücretli mi?",
    "q.3.a": "Hayır. VeltOS ücretsiz ve açık kaynaktır; üzerine kurulduğu yazılımlar da öyle.",
    "q.4.q": "Günlük kullanıma hazır mı?",
    "q.4.a": "Henüz değil: 0.1 sürümü test için bir ön alfadır. Bir sanal makinede ya da yedek bir bilgisayarda deneyin, bulduklarınızı GitHub'da bize bildirin.",
    "q.5.q": "Güncelleştirmeler nereden gelir?",
    "q.5.a": "Debian'ın imzalı arşivlerinden, VeltOS Mağaza ve Ayarlar üzerinden; VeltOS'un kendi paketleri bu depodaki koddan derlenir.",
    "q.6.q": "Hangi dilleri konuşur?",
    "q.6.a": "VeltOS'un kendi pencerelerinin hepsinde Türkçe ve İngilizce. Debian ve KDE parçaları çok daha fazla dilde kullanılabilir.",
    "foot.tag": "Bilgisayarınız. Sınırsız.",
    "foot.source": "Kaynak kodu",
    "foot.status": "Proje durumu",
    "foot.issues": "Sorun bildirin",
    "foot.legal": "VeltOS; Debian, KDE Plasma, LibreOffice, Firefox, Thunderbird, Wine ve Calamares üzerine kurulu bağımsız bir projedir. Microsoft ile bağlantılı değildir ve Microsoft tarafından desteklenmez; Windows, Word, Excel, PowerPoint ve Outlook, Microsoft Corporation'ın ticari markalarıdır ve burada yalnızca VeltOS'un neye benzediğini anlatmak için anılır. VeltOS görselleri © VeltOS Geliştiricileri, CC BY-SA 4.0.",
    "lb.close": "Kapat"
  };
  var TITLES = {
    en: "VeltOS — Your PC. No Limits.",
    tr: "VeltOS — Bilgisayarınız. Sınırsız."
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
    var decimals = parseInt(el.getAttribute("data-decimals") || "0", 10);
    var suffix = el.getAttribute("data-suffix") || "";
    if (reduced) { el.textContent = target.toFixed(decimals) + suffix; return; }
    var start = null;
    function frame(now) {
      if (start === null) start = now;
      var p = Math.min(1, (now - start) / 1400);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(decimals) + suffix;
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
