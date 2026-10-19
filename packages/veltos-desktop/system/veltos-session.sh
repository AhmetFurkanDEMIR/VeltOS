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

# Per-user defaults KDE has no system-wide setting for (application style,
# File Explorer side bar). Created once; a user's own files are kept.
if [ ! -e "${XDG_CONFIG_HOME:-$HOME/.config}/Kvantum/kvantum.kvconfig" ] ||
   [ ! -e "${XDG_DATA_HOME:-$HOME/.local/share}/user-places.xbel" ] ||
   [ ! -e "${XDG_DATA_HOME:-$HOME/.local/share}/kxmlgui5/dolphin/dolphinui.rc" ]; then
    /usr/libexec/veltos/session-defaults || true
fi

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
