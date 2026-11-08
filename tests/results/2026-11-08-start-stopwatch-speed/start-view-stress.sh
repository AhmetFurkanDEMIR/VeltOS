#!/bin/sh
# Dev aid (VM only, in the user's session): switch Start's "All" view many
# times while Start is open, through Plasma's script API (the same
# configuration key the View menu writes), and report whether plasmashell
# survived. Usage: start-view-stress.sh [rounds] [delay]
rounds="${1:-20}"; delay="${2:-0.3}"
before="$(pidof plasmashell)"
i=0
while [ "$i" -lt "$rounds" ]; do
    for view in list category grid category list grid; do
        qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "
for (const p of panels()) for (const w of p.widgets('org.veltos.startmenu')) {
    w.currentConfigGroup = ['General']; w.writeConfig('allAppsView', '$view'); }" >/dev/null 2>&1
        sleep "$delay"
    done
    i=$((i + 1))
done
after="$(pidof plasmashell)"
echo "plasmashell before=$before after=$after"
