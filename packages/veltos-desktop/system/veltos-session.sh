# VeltOS Plasma session setup. Plasma sources this file (installed in
# /etc/xdg/plasma-workspace/env/) when a session starts, before any
# application runs.

# Applications carry their VeltOS names ("File Explorer", "Settings", ...)
# in /var/lib/veltos/xdg/applications (written by
# /usr/libexec/veltos/update-app-names); that directory must come first.
case ":${XDG_DATA_DIRS:-}:" in
    *:/var/lib/veltos/xdg:*) ;;
    *) export XDG_DATA_DIRS="/var/lib/veltos/xdg:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" ;;
esac

# Window animations like Windows 11 also without 3D acceleration: KWin
# turns its animations off when it renders in software (llvmpipe, most
# virtual machines), so windows popped up and vanished without any
# animation there (VM, 2026-10-20). With a real GPU this changes nothing.
export KWIN_EFFECTS_FORCE_ANIMATIONS=1

# Per-user defaults KDE has no system-wide setting for (application style,
# File Explorer side bar). Created once; a user's own files are kept.
if [ ! -e "${XDG_CONFIG_HOME:-$HOME/.config}/Kvantum/kvantum.kvconfig" ] ||
   [ ! -e "${XDG_DATA_HOME:-$HOME/.local/share}/user-places.xbel" ] ||
   [ ! -e "${XDG_DATA_HOME:-$HOME/.local/share}/kxmlgui5/dolphin/dolphinui.rc" ]; then
    /usr/libexec/veltos/session-defaults || true
fi

# Desktop and taskbar right-click menus without KDE's widget and panel
# editing entries (read by plasmashell when it starts, so set here).
/usr/libexec/veltos/context-menus || true

# The Terminal follows the light/dark theme, like Windows Terminal.
case "$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage 2>/dev/null)" in
    *.dark) /usr/libexec/veltos/terminal-theme dark ;;
    *) /usr/libexec/veltos/terminal-theme light ;;
esac >/dev/null 2>&1 || true

# GTK programs (Firefox, ...) use the VeltOS GTK theme: Breeze with the
# Windows 11 caption buttons of the window frames. Breeze, KDE's default,
# is switched over; any other theme a user picked is kept.
for veltos_gtk in gtk-3.0 gtk-4.0; do
    veltos_ini="${XDG_CONFIG_HOME:-$HOME/.config}/$veltos_gtk/settings.ini"
    if [ ! -e "$veltos_ini" ]; then
        mkdir -p "${veltos_ini%/*}" && printf '[Settings]\ngtk-theme-name=VeltOS\n' > "$veltos_ini"
    elif grep -q '^gtk-theme-name=Breeze\(-Dark\)\?$' "$veltos_ini"; then
        sed -i 's/^gtk-theme-name=Breeze\(-Dark\)\?$/gtk-theme-name=VeltOS/' "$veltos_ini"
    fi
done
unset veltos_gtk veltos_ini

# "This PC" and "Recycle Bin" on the desktop, like Windows. They cannot be
# removed for good: a deleted one comes back at the next sign-in. The
# Store icon is put there once; a user may delete it.
veltos_desktop="$( . "${XDG_CONFIG_HOME:-$HOME/.config}/user-dirs.dirs" 2>/dev/null
                   printf '%s' "${XDG_DESKTOP_DIR:-$HOME/Desktop}" )"
mkdir -p "$veltos_desktop"
for veltos_icon in "${VELTOS_DESKTOP_ICONS:-/usr/share/veltos/desktop}"/*.desktop; do
    veltos_name="${veltos_icon##*/}"
    veltos_once="${XDG_STATE_HOME:-$HOME/.local/state}/veltos/desktop-$veltos_name"
    case "$veltos_name" in
        recycle-bin.desktop|this-pc.desktop) ;;
        *) [ -e "$veltos_once" ] && continue
           mkdir -p "${veltos_once%/*}" && : > "$veltos_once" ;;
    esac
    if [ ! -e "$veltos_desktop/$veltos_name" ]; then
        # Executable: Plasma starts only trusted (executable) launchers.
        install -m 755 "$veltos_icon" "$veltos_desktop/" 2>/dev/null || true
    fi
    # The desktop lists its icons by date (layout script, session-fixups):
    # fixed old dates keep these first, in Windows' order, and new files
    # after them. ("Install VeltOS" in the live system has the oldest.)
    case "$veltos_name" in
        recycle-bin.desktop) touch -d @2 "$veltos_desktop/$veltos_name" 2>/dev/null || true ;;
        this-pc.desktop) touch -d @3 "$veltos_desktop/$veltos_name" 2>/dev/null || true ;;
        veltos-store.desktop) touch -d @4 "$veltos_desktop/$veltos_name" 2>/dev/null || true ;;
    esac
done
unset veltos_desktop veltos_icon veltos_name veltos_once

# Program names inside the programs ("Home — File Explorer" instead of
# "Home — Dolphin"): VeltOS message catalogs for the pseudo-languages
# en@veltos / tr@veltos translate only those names and come first; every
# other text falls through to the real language.
case "${LANGUAGE:-}" in
    *@veltos*) ;;
    *)
        veltos_lang="${LANGUAGE:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}"
        case "$veltos_lang" in
            tr*) export LANGUAGE="tr@veltos:${LANGUAGE:-tr}" ;;
            en*) export LANGUAGE="en@veltos:${LANGUAGE:-en_US}" ;;
        esac
        unset veltos_lang
        ;;
esac
