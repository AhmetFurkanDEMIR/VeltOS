// VeltOS default desktop layout (Plasma 6 layout script).
//
// Plasma runs this once, the first time a user starts a Plasma session, via
// the look-and-feel package named in kdeglobals [KDE] LookAndFeelPackage.
// Existing users are never touched.
//
// Layout: one bottom taskbar. Two flexible spacers keep the start button and
// the task manager centred (Windows 11 style); tray and clock sit on the right.

var wallpaper = "file:///usr/share/wallpapers/VeltOS/";

var desktopsArray = desktopsForActivity(currentActivity());
for (var i = 0; i < desktopsArray.length; i++) {
    var desktop = desktopsArray[i];
    desktop.wallpaperPlugin = "org.kde.image";
    desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktop.writeConfig("Image", wallpaper);
}

var panel = new Panel;
panel.location = "bottom";
// Even number of pixels; the panel size spinbox only shows even values.
panel.height = 2 * Math.floor(gridUnit * 2.6 / 2);
if ("floating" in panel) {
    panel.floating = false;
}

panel.addWidget("org.kde.plasma.panelspacer");

// VeltOS Start (Windows 11 style menu, packaged with veltos-desktop).
// The Meta key opens it because it provides org.kde.plasma.launchermenu.
var start = panel.addWidget("org.veltos.startmenu");
start.currentConfigGroup = ["Shortcuts"];
start.writeConfig("global", "Alt+F1");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
// Pinned like a fresh Windows 11 PC: File Explorer, browser, Settings.
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "applications:firefox-esr.desktop",
    "applications:veltos-settings.desktop"
]);

panel.addWidget("org.kde.plasma.panelspacer");

// Tray: network, sound, battery and notifications stay visible; everything
// else goes behind the "^" overflow arrow, as on Windows 11.
var systray = panel.addWidget("org.kde.plasma.systemtray");
var systrayContainmentId = systray.readConfig("SystrayContainmentId");
if (systrayContainmentId) {
    var tray = desktopById(systrayContainmentId);
    tray.currentConfigGroup = ["General"];
    tray.writeConfig("hiddenItems", [
        "org.kde.plasma.brightness",
        "org.kde.plasma.clipboard",
        "org.kde.plasma.devicenotifier",
        "org.kde.plasma.manage-inputmethod",
        "org.kde.plasma.vault",
        "org.kde.kdeconnect",
        "org.kde.kscreen",
        "org.kde.plasma.printmanager"
    ]);
}

// Clock like Windows 11: time above the date, normal text size, instead of
// text scaled to the panel height.
var clock = panel.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("autoFontAndSize", false);
clock.writeConfig("fontSize", 10);
clock.writeConfig("dateDisplayFormat", 2);   // below the time
clock.writeConfig("dateFormat", "shortDate");
clock.writeConfig("showSeconds", 0);
// No "show desktop" button: Windows 11 has none visible (Meta+D works).
