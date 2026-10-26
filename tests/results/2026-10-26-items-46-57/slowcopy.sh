#!/bin/sh
# Dev aid: run File Explorer's copy window with the disk read limited to
# 60 MB/s (cgroup io.max), like a USB stick, so the window can be seen.
# Usage (root): slowcopy.sh DEST SOURCE...
pid=$(pgrep -u velt -x plasmashell | head -n1)
env_args=""
for name in WAYLAND_DISPLAY XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS QT_QPA_PLATFORMTHEME XDG_CURRENT_DESKTOP LANG HOME; do
    value=$(tr '\0' '\n' < /proc/$pid/environ | sed -n "s/^$name=//p")
    [ -n "$value" ] && env_args="$env_args -E $name=$value"
done
sync
echo 3 > /proc/sys/vm/drop_caches
# shellcheck disable=SC2086
systemd-run --uid=velt --collect -p "IOReadBandwidthMax=/dev/vda 60M" -p "IOWriteBandwidthMax=/dev/vda 60M" \
    $env_args veltos-explorer --transfer copy "$@"
