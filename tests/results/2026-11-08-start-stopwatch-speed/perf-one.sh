#!/usr/bin/env bash
# Dev aid (git-ignored): one scene of perf-scenes.sh, repeated N times.
#   perf-one.sh SCENE [N]   SCENE: start-open-close | start-open-idle | quick-settings | search-typing
set -uo pipefail
cd "$(dirname "$0")/../.."
vmx() { timeout 100 bash build/run.sh vm exec "$1" 2>/dev/null | tr -d '\r'; }
case "$1" in
    start-open-close) seconds=20; actions="key:meta_l sleep:1.6 key:esc sleep:1.6 key:meta_l sleep:1.6 key:esc sleep:1.6 key:meta_l sleep:1.6 key:esc sleep:1.6 key:meta_l sleep:1.6 key:esc sleep:1.6 key:meta_l sleep:1.6 key:esc sleep:1.6 key:meta_l sleep:1.6 key:esc sleep:1.6" ;;
    start-open-idle) seconds=15; actions="key:meta_l sleep:15 key:esc" ;;
    quick-settings) seconds=15; actions="click:1730,1056 sleep:2 key:esc sleep:1 click:1730,1056 sleep:2 key:esc sleep:1 click:1730,1056 sleep:2 key:esc sleep:1 click:1730,1056 sleep:2 key:esc sleep:3" ;;
    search-typing) seconds=15; actions="click:780,1056 sleep:2 type:settings sleep:1 key:backspace key:backspace key:backspace sleep:1 type:ngs sleep:1 type:abc sleep:2 key:esc sleep:7" ;;
esac
for _ in $(seq 1 "${2:-1}"); do
    timeout 60 bash build/run.sh vm do "key:esc move:100,300 sleep:2" >/dev/null 2>&1
    vmx "rm -f /tmp/m.txt; nohup sh /usr/local/lib/veltos-dev/measure-kwin.sh $seconds /tmp/m.txt >/dev/null 2>&1 &"
    timeout 200 bash build/run.sh vm do "move:100,300 $actions" >/dev/null 2>&1
    sleep 2
    echo "$1: $(vmx 'cat /tmp/m.txt')"
done
