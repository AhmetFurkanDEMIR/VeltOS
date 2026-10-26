# 2026-10-26 — Product owner's items 46-57 in the dev VM

QEMU dev VM, live system of ISO `20261026-063914` with the rebuilt
veltos-desktop, veltos-settings, veltos-explorer, veltos-maps, veltos-ai,
veltos-weather and veltos-fluent-icons installed (`dpkg -i`), Plasma
restarted (and the session restarted once through SDDM so kglobalaccel and
session-fixups ran). English UI, 1920x1080, no battery (QEMU has none and
Debian's kernel has no `test_power` module).

| Item | What was seen | Picture |
|---|---|---|
| 46 Battery opens Power & battery | The battery button at the bottom left of Quick Settings opened Settings > System > Power & battery | `01` |
| 47 No KRunner box | Typing on the desktop, Alt+Space and Alt+F2 opened nothing; no `krunner` process (`/etc/xdg/krunnerrc`, kglobalaccel override) | — |
| 48 Hidden icons hover | The see-through box behind the "^" arrow on hover | `03` |
| 49 Power modes | Settings: one drop-down on a PC without a battery ("Plugged in" and "On battery" rows with one), Best performance greyed where power-profiles-daemon offers none, the effective mode shown; Quick Settings: three mode cards with Plugged in / On battery tabs on battery PCs; choosing Balanced or Best power efficiency changed `powerprofilesctl get` (from inside the session; started outside it, polkit refuses and Settings says so). The tile shows the active mode | `04`, `05` |
| 50 Start line | No line beside Start's scroll bar (Plasma theme without `private-hint-show-separator`) | `06` |
| 51 VeltOS AI | The button after the clock (also added once to an existing taskbar, before the show-desktop corner), opening and closing the pane; its menu (settings, hide); Settings > Apps > VeltOS AI (service, key, model, actions, taskbar button on/off) | `02`, `07`-`09` |
| 52 Weather | °C on an en_US system | `10` |
| 53 Maps and location | Google's pages in the app's language, the map over the whole window, floating controls, InfoBars; a second start brings the one window forward; "Set default" from Settings saved the map's centre (mode 600) and Settings > Location showed it; the privacy text names beaconDB (Debian's GeoClue default) | `11`-`13` |
| 54 "plasmashell" windows | Shift+Delete on the desktop: File Explorer's Windows 11 "Delete File"; paste of a desktop file onto the desktop: "Report - Copy.txt" without KDE's "File Already Exists"; plasmashell's desktop entry named "File Explorer" (taskbar, notifications, not-responding window) | `14` |
| 55 Copy window | `veltos-explorer --transfer`: "19% complete", More details with the speed graph (58.8 MB/s with the disk limited to 60 MB/s by `slowcopy.sh`), time and items remaining, Pause ("Paused - 48% complete"), Cancel (no partial file left), "Replace or Skip Files" | `15`-`18` |
| 56 Battery in the tray | The battery icon on the taskbar and "Plugged in" at the bottom left of Quick Settings on a PC without a battery | `01`, `02` |
| 57 Removable drive icon | The new drive in the local disk's family with the USB symbol and a blue light, in This PC (a `scsi_debug` removable disk) | `19`, `20` |

Not seen: a real battery (level, charging, the automatic switch between
plugged-in and battery modes), real AI services (no keys), a real
location fix, dragging files onto the desktop (still Plasma's menu and KIO).
