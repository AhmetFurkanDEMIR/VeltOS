#!/usr/bin/env bash
# Dev aid (git-ignored; dev VM, installed system): CPU of kwin_wayland and
# plasmashell (one core = 100 %) in typical moments of the shell, measured
# by /usr/local/lib/veltos-dev/measure-kwin.sh while vm do drives the UI.
# Usage: out/vm/perf-scenes.sh LABEL   (writes out/vm/perf-LABEL.txt)
set -uo pipefail
cd "$(dirname "$0")/../.."
label="${1:-run}"
result="out/vm/perf-$label.txt"
: > "$result"
vmx() { timeout 100 bash build/run.sh vm exec "$1" 2>/dev/null | tr -d '\r'; }
scene() {
    local name="$1" seconds="$2" actions="$3"
    vmx "rm -f /tmp/m.txt; nohup sh /usr/local/lib/veltos-dev/measure-kwin.sh $seconds /tmp/m.txt >/dev/null 2>&1 &"
    timeout 200 bash build/run.sh vm do "$actions" >/dev/null 2>&1
    sleep 2
    echo "$name: $(vmx 'cat /tmp/m.txt')" | tee -a "$result"
}
timeout 60 bash build/run.sh vm do "key:esc move:960,500 sleep:3" >/dev/null 2>&1
scene idle 15 "sleep:16"
scene start-open-close 20 "key:meta_l sleep:1.6 key:esc sleep:1.6 key:meta_l sleep:1.6 key:esc sleep:1.6 key:meta_l sleep:1.6 key:esc sleep:1.6 key:meta_l sleep:1.6 key:esc sleep:1.6 key:meta_l sleep:1.6 key:esc sleep:1.6 key:meta_l sleep:1.6 key:esc sleep:1.6"
scene start-scroll 20 "key:meta_l sleep:2 wheeldown:960,700,3 sleep:0.6 wheelup:960,700,3 sleep:0.6 wheeldown:960,700,3 sleep:0.6 wheelup:960,700,3 sleep:0.6 wheeldown:960,700,3 sleep:0.6 wheelup:960,700,3 sleep:0.6 wheeldown:960,700,3 sleep:0.6 wheelup:960,700,3 sleep:0.6 wheeldown:960,700,3 sleep:0.6 wheelup:960,700,3 sleep:0.6 key:esc sleep:3"
scene start-open-idle 15 "key:meta_l sleep:15 key:esc"
scene search-typing 15 "click:780,1056 sleep:2 type:settings sleep:1 key:backspace key:backspace key:backspace sleep:1 type:ngs sleep:1 type:abc sleep:2 key:esc sleep:7"
scene quick-settings 15 "click:1730,1056 sleep:2 key:esc sleep:1 click:1730,1056 sleep:2 key:esc sleep:1 click:1730,1056 sleep:2 key:esc sleep:1 click:1730,1056 sleep:2 key:esc sleep:3"
scene taskbar-hover 15 "move:900,1056 sleep:0.5 move:1000,1056 sleep:0.5 move:1060,1056 sleep:0.5 move:1110,1056 sleep:0.5 move:1160,1056 sleep:0.5 move:1210,1056 sleep:0.5 move:1260,1056 sleep:0.5 move:955,1056 sleep:0.5 move:1005,1056 sleep:0.5 move:1060,1056 sleep:0.5 move:960,500 sleep:8"
cat "$result"
