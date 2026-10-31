# 2026-10-31 — Items 106-107: no KDE windows with the "W" icon, the pointer follows the theme

Dev VM: QEMU/KVM, live system of ISO `veltos-1.1-dev3` with the rebuilt
packages (veltos-explorer, -settings, -desktop, -fluent-icons, -ai,
-photos, -winapps) installed with `dpkg -i`. Simulated Wi-Fi:
`out/vm/wifisim.sh` (mac80211_hwsim, hostapd "VeltOS-Home" with key
veltos1234, dnsmasq). `winlog.js` is the KWin script that printed every new
window's app id to the journal (`journalctl _UID=1000 | grep winlog`).

## Before (1.1-dev3)

- `01`: a wrong Wi-Fi key in Quick Settings: kded's "Wi-Fi password dialog"
  (plasma-nm, KDE logo; app id `org.kde.kded6`).
- `02`: a launcher from Downloads opened the way File Explorer did
  (`kioclient exec`): "Warning — KIO Client" with the Wayland "W" icon in
  the title bar and on the taskbar (app id `org.kde.kioclient`, no desktop
  file); plasma-nm's "No secrets were provided" notification.
- `03`: the desktop portal's Account request: KDE's "Share Information".

## After

- `04`: the same wrong key: VeltOS' "Connect to a network" window (the
  VeltOS network agent) with "The network security key isn't correct";
  the right key connected (NetworkManager stored it: `nmcli -s`).
- `05`: the launcher: "Open File - Security Warning"; Run started it.
- `06`: deleting a file the user may not delete (`--remove`): "Couldn't
  delete" with the reason. `--recycle` moved a file to the Recycle Bin
  (`~/.local/share/Trash/info/t3.txt.trashinfo`).
- `07`, `08`: the portal's Account and Access requests in VeltOS' question
  window; Allow answered `(uint32 0, @a{sv} {})`.
- `09`, `10`: Settings > Accessibility > Mouse pointer (style tiles,
  recommended colours, size).
- `11`-`13`: the real pointer (`spectacle -b -n -f -p`): custom orange,
  white in dark mode (style "Colour mode", switched by the light/dark
  command), the dark pointer in light mode. Sizes 48 and 96 applied too
  (96 px needed veltos-fluent-icons' new cursor sizes).
- `14`, `15` (item 92, standard user's prompt): with the live system's
  allow-all polkit rule moved away, App Installer's Install asked in
  VeltOS' User Account Control window and installed the package.

Not tried: an enterprise (802.1X) or WEP network, a USB stick's own
trash folder, a Linux program from Downloads, screen sharing (KDE's
chooser stays).
