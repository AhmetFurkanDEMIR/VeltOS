#!/bin/sh
# Dev aid (builder container): GRUB 2.12 with VeltOS' start screen in QEMU.
# Checks that the hidden wait shows start-hint.tga and that F6 starts the
# "VeltOS Recovery" entry, which puts start.tga back.
set -eu
apt-get update -qq >/dev/null 2>&1
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    grub-pc-bin grub-common xorriso mtools qemu-system-x86 python3 >/dev/null 2>&1
work=/tmp/grubtest
rm -rf "$work"; mkdir -p "$work/iso/boot/grub/veltos" "$work/deb"
dpkg-deb -x /out/packages/veltos-boot_*_all.deb "$work/deb"
VELTOS_START_SCREEN_ASSETS="$work/deb/usr/share/veltos-boot/start-screen" \
    python3 "$work/deb/usr/libexec/veltos-boot/start-screen" --mode 1024x768 --lang "${LANG_TEST:-tr_TR.UTF-8}" \
    --out "$work/iso/boot/grub/veltos"
cat > "$work/iso/boot/grub/grub.cfg" <<'EOF'
insmod all_video
insmod gfxterm
set gfxmode=1024x768
terminal_output gfxterm
set color_normal=black/black
set color_highlight=black/black
set timeout_style=hidden
set timeout=20
function veltos_start_screen {
  if [ -n "${veltos_screen}" ]; then background_image -m stretch "${veltos_screen}"; fi
}
menuentry 'VeltOS' --id 'gnulinux-simple' {
  veltos_start_screen
  set color_normal=white/black
  echo "VELTOS STARTED"
  sleep 60
}
menuentry 'VeltOS Recovery' --class veltos --hotkey=f6 --id 'veltos-recovery' {
  veltos_start_screen
  set color_normal=white/black
  echo "RECOVERY STARTED"
  sleep 60
}
if [ "${timeout_style}" = hidden ]; then
  insmod tga
  if background_image -m stretch "${prefix}/veltos/start-hint.tga"; then
    set veltos_screen="${prefix}/veltos/start.tga"
    clear
  fi
fi
EOF
grub-mkrescue -o "$work/test.iso" "$work/iso" >/dev/null 2>&1
qemu-system-x86_64 -m 512 -display none -vga std -cdrom "$work/test.iso" \
    -qmp unix:$work/qmp.sock,server=on,wait=off -daemonize
python3 - "$work/qmp.sock" /out/grubtest <<'PY'
import json, socket, sys, time
sock = socket.socket(socket.AF_UNIX)
for _ in range(50):
    try:
        sock.connect(sys.argv[1]); break
    except OSError:
        time.sleep(0.2)
f = sock.makefile("rw")
def cmd(name, **args):
    f.write(json.dumps({"execute": name, "arguments": args}) + "\n"); f.flush()
    while True:
        reply = json.loads(f.readline())
        if "return" in reply or "error" in reply:
            return reply
f.readline(); cmd("qmp_capabilities")
time.sleep(8)
cmd("screendump", filename=sys.argv[2] + "/waiting.ppm")
cmd("send-key", keys=[{"type": "qcode", "data": "f6"}])
time.sleep(3)
cmd("screendump", filename=sys.argv[2] + "/after-f6.ppm")
cmd("quit")
PY
echo done
