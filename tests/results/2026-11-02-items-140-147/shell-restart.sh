#!/bin/sh
# Dev aid (VM only, in the user's session): restart plasmashell with its
# theme caches cleared, and load the blur and contrast effects as on real
# graphics cards.
rm -rf "$HOME"/.cache/plasma-svgelements* "$HOME"/.cache/plasma_theme_* "$HOME"/.cache/ksvg-elements* \
    "$HOME"/.cache/plasmashell/qmlcache
qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.loadEffect blur >/dev/null
qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.loadEffect contrast >/dev/null
systemctl --user restart plasma-plasmashell.service
sleep 8
