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
    // Desktop icons top to bottom from the top-left corner, like Windows
    // (folder view: arrangement 1 = columns), in date order (2 = KDirModel's
    // modified-time column) with folders not first: the Recycle Bin, This PC
    // and the Store have fixed old dates (veltos-session.sh), new files
    // follow them.
    desktop.currentConfigGroup = ["General"];
    desktop.writeConfig("arrangement", 1);
    desktop.writeConfig("sortMode", 2);
    desktop.writeConfig("sortDirsFirst", false);
    // No hover buttons on the icons (Plasma's selection markers and folder
    // preview pop-ups): Windows shows none.
    desktop.writeConfig("selectionMarkers", false);
    desktop.writeConfig("popups", false);
}

var panel = new Panel;
panel.location = "bottom";
// 48 pixels high like the Windows 11 taskbar (more with large fonts).
panel.height = Math.max(48, 2 * Math.floor(gridUnit * 2.6 / 2));
if ("floating" in panel) {
    panel.floating = false;
}
// See-through like Windows 11 (with the blur effect when the graphics
// driver supports it), also while a window is maximized.
if ("opacity" in panel) {
    panel.opacity = "translucent";
}

panel.addWidget("org.kde.plasma.panelspacer");

// VeltOS Start (Windows 11 style menu, packaged with veltos-desktop).
// The Meta key opens it because it provides org.kde.plasma.launchermenu.
var start = panel.addWidget("org.veltos.startmenu");
start.currentConfigGroup = ["Shortcuts"];
start.writeConfig("global", "Alt+F1");

// Search box and Task View button next to Start, as on Windows 11.
panel.addWidget("org.veltos.search");
panel.addWidget("org.veltos.taskview");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
// Pinned like a fresh Windows 11 PC, left to right (product owner,
// 2026-10-22): File Explorer, the browser, Settings, the Store, Camera,
// Photos and Media Player. Users pin and unpin apps themselves later.
tasks.writeConfig("launchers", [
    "applications:veltos-explorer.desktop",
    "applications:firefox-esr.desktop",
    "applications:veltos-settings.desktop",
    "applications:veltos-store.desktop",
    "applications:veltos-camera.desktop",
    "applications:veltos-photos.desktop",
    "applications:veltos-media.desktop"
]);
// Each virtual desktop shows only its own windows, as on Windows.
tasks.writeConfig("showOnlyCurrentDesktop", true);

panel.addWidget("org.kde.plasma.panelspacer");

// Tray like Windows 11: network, sound, brightness, Bluetooth and battery
// are not tray icons but one Quick Settings button (org.veltos.quicksettings,
// added below); the remaining tray items sit behind the "^" arrow except
// notifications and the keyboard layout. knownItems lists everything Plasma
// knows, so it does not switch the excluded items back on as "new".
var systray = panel.addWidget("org.kde.plasma.systemtray");
var systrayContainmentId = systray.readConfig("SystrayContainmentId");
if (systrayContainmentId) {
    var tray = desktopById(systrayContainmentId);
    tray.currentConfigGroup = ["General"];
    tray.writeConfig("knownItems", [
        "org.kde.kdeconnect", "org.kde.kscreen", "org.kde.kupapplet",
        "org.kde.plasma.battery", "org.kde.plasma.bluetooth", "org.kde.plasma.brightness",
        "org.kde.plasma.cameraindicator", "org.kde.plasma.clipboard",
        "org.kde.plasma.devicenotifier", "org.kde.plasma.keyboardlayout",
        "org.kde.plasma.manage-inputmethod", "org.kde.plasma.mediacontroller",
        "org.kde.plasma.networkmanagement", "org.kde.plasma.notifications",
        "org.kde.plasma.printmanager", "org.kde.plasma.vault", "org.kde.plasma.volume"
    ]);
    tray.writeConfig("extraItems", [
        "org.kde.plasma.cameraindicator", "org.kde.plasma.clipboard",
        "org.kde.plasma.devicenotifier", "org.kde.plasma.keyboardlayout",
        "org.kde.plasma.manage-inputmethod", "org.kde.plasma.mediacontroller",
        "org.kde.plasma.notifications", "org.kde.plasma.printmanager"
    ]);
    tray.writeConfig("hiddenItems", [
        "org.kde.plasma.clipboard", "org.kde.plasma.devicenotifier",
        "org.kde.plasma.manage-inputmethod", "org.kde.plasma.mediacontroller",
        "org.kde.plasma.printmanager"
    ]);
}

// Quick Settings (Wi-Fi, Bluetooth, sound, brightness, battery).
panel.addWidget("org.veltos.quicksettings");

// Clock like Windows 11: time above the date in the same small size; it
// opens the notification centre and the calendar, also with Win+N.
var clock = panel.addWidget("org.veltos.clock");
clock.globalShortcut = "Meta+N";

// The thin "show desktop" area at the right end, as on Windows 11.
panel.addWidget("org.veltos.showdesktop");

// Locked like the Windows 11 taskbar: no widgets added, moved or removed,
// and no KDE settings dialogs (see system/session-fixups, which also locks
// the tray's items at sign-in).
panel.widgets().forEach(function (widget) {
    widget.locked = true;
});
panel.locked = true;
