#!/usr/bin/env bash
# Dev aid (git-ignored; dev VM, installed system, user jordanl): start every
# VeltOS app in the session, check it is running after a few seconds, close
# it with Alt+F4 as a user would, and report crashes (systemd-coredump) and
# apps that did not end. Usage: out/vm/app-exit-test.sh [app ...]
set -uo pipefail
cd "$(dirname "$0")/../.."
vmx() { timeout 100 bash build/run.sh vm exec "$1" 2>/dev/null | tr -d '\r'; }
apps=("$@")
if [ ${#apps[@]} -eq 0 ]; then
    apps=(veltos-settings veltos-explorer veltos-clock veltos-calendar veltos-taskmanager veltos-calculator
          veltos-notepad veltos-photos veltos-media veltos-pdf veltos-mail "veltos-office word" veltos-archive
          veltos-camera veltos-store veltos-disks veltos-graphics veltos-lighting veltos-weather veltos-maps
          "veltos-ai --window")
fi
since="$(vmx "date '+%Y-%m-%d %H:%M:%S'")"
for app in "${apps[@]}"; do
    name="${app%% *}"
    vmx "systemd-run --machine=jordanl@.host --user --collect --slice=app.slice -p KillMode=process $app >/dev/null 2>&1"
    sleep 9
    pid="$(vmx "pgrep -u jordanl -f '[/]usr/bin/$name( |$)' | head -1")"
    [ -z "$pid" ] && pid="$(vmx "pgrep -u jordanl -f '[p]ython3.*$name' | head -1")"
    timeout 60 bash build/run.sh vm do "key:alt+f4 sleep:3" >/dev/null 2>&1
    left="$(vmx "pgrep -u jordanl -f '[/]usr/bin/$name( |$)|[p]ython3.* -m ${name//-/_}( |$)' | tr '\n' ' '")"
    echo "$app: started pid=${pid:-none} after-close=[${left}]"
    if [ -n "$left" ]; then
        vmx "pkill -u jordanl -f '[/]usr/bin/$name( |$)'"
        sleep 1
    fi
done
echo "--- core dumps since $since"
vmx "coredumpctl list --no-pager --since '$since' 2>/dev/null | tail -n +2"
