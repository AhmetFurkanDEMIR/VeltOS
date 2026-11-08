#!/bin/sh
# Dev aid (VM only, in the user's session): Start's view switch stress at
# several screen sizes and scales (out/vm/start-view-stress.sh), Start
# opened through plasmashell's launcher call. Prints one line per case.
out=Virtual-1
for case in "1920x1080 1" "1920x1080 1.25" "1920x1080 1.5" "1360x768 1" "1280x768 1" "1280x960 1" \
            "1024x768 1" "1440x900 1" "1680x1050 1.25" "2048x1152 1.5" "1280x1024 1.25" "1920x1200 1.25" \
            "1440x900 1.25" "1360x768 1.25"; do
    set -- $case
    kscreen-doctor "output.$out.mode.$1@60" "output.$out.scale.$2" >/dev/null 2>&1 \
        || kscreen-doctor "output.$out.mode.$1" "output.$out.scale.$2" >/dev/null 2>&1
    sleep 4
    qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.activateLauncherMenu >/dev/null 2>&1
    sleep 2
    result="$(sh /usr/local/lib/veltos-dev/start-view-stress.sh 4 0.12)"
    echo "$1 x$2: $result"
    qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.activateLauncherMenu >/dev/null 2>&1
    sleep 1
done
kscreen-doctor "output.$out.mode.1920x1080@60" "output.$out.scale.1" >/dev/null 2>&1
