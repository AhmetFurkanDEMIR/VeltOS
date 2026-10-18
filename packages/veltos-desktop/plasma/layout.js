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

var kickoff = panel.addWidget("org.kde.plasma.kickoff");
kickoff.currentConfigGroup = ["General"];
kickoff.writeConfig("icon", "veltos-logo");
kickoff.currentConfigGroup = ["Shortcuts"];
kickoff.writeConfig("global", "Alt+F1");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "applications:firefox-esr.desktop",
    "applications:org.kde.konsole.desktop",
    "applications:systemsettings.desktop"
]);

panel.addWidget("org.kde.plasma.panelspacer");

panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.kde.plasma.digitalclock");
panel.addWidget("org.kde.plasma.showdesktop");
