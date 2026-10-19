# VeltOS live session settings. Plasma sources this file (installed in
# /etc/xdg/plasma-workspace/env/) at session start; it only acts when the
# system runs from the install medium. (This package is removed from
# installed systems by the installer.)
#
# Nobody knows the live user's password, so the screen must never lock, and
# the computer should not sleep or turn the screen off while someone reads
# the installer or a copy is running.
if [ -d "${VELTOS_LIVE_MEDIUM:-/run/live/medium}" ]; then  # variable: for tests
    veltos_cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
    mkdir -p "$veltos_cfg"
    if [ ! -e "$veltos_cfg/kscreenlockerrc" ]; then
        printf '[Daemon]\nAutolock=false\nLockOnResume=false\n' > "$veltos_cfg/kscreenlockerrc"
    fi
    if [ ! -e "$veltos_cfg/powerdevilrc" ]; then
        for veltos_profile in AC Battery LowBattery; do
            printf '[%s][Display]\nDimDisplayWhenIdle=false\nTurnOffDisplayWhenIdle=false\nLockBeforeTurnOffDisplay=false\n\n' "$veltos_profile"
            printf '[%s][SuspendAndShutdown]\nAutoSuspendAction=0\n\n' "$veltos_profile"
        done > "$veltos_cfg/powerdevilrc"
        unset veltos_profile
    fi
    unset veltos_cfg
fi
