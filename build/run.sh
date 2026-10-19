#!/usr/bin/env bash
# VeltOS developer entry point. Every step runs inside the veltos-builder
# container, so the host only needs Docker (Linux, macOS, or Windows with
# Docker Desktop + Git Bash). See docs/build-guide.md.
#
#   build/run.sh image        build the builder container image
#   build/run.sh packages [name...]  build the VeltOS .deb packages into
#                             out/packages (all, or only the named ones)
#   build/run.sh iso          build packages + the live ISO into out/iso
#   build/run.sh test [mode]  boot the newest ISO in QEMU/KVM and verify it
#                             (mode: uefi (default), bios, secureboot)
#   build/run.sh test-winapps [fixture]  install a real Windows program
#                             in the newest ISO via the VeltOS runner
#   build/run.sh preview [actions]  dev aid: try out/packages/*.deb in the
#                             newest ISO in a VM and take screenshots
#   build/run.sh vm ...       long-running VM driven step by step (install tests)
#   build/run.sh shell        interactive shell in the builder container
#   build/run.sh clean        delete the build volume (forces a cold build)
set -euo pipefail

# Git Bash on Windows rewrites /paths in arguments; container paths must stay.
export MSYS_NO_PATHCONV=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Docker Desktop on Windows wants C:/... style paths for bind mounts.
if HOST_ROOT="$(cd "$REPO_ROOT" && pwd -W 2>/dev/null)"; then :; else HOST_ROOT="$REPO_ROOT"; fi

IMAGE="${VELTOS_BUILDER_IMAGE:-veltos-builder:dev}"
# live-build needs a real Linux filesystem (device nodes, chroot, hard links),
# so the build tree lives in a named volume, never on the bind-mounted repo.
VOLUME="${VELTOS_BUILD_VOLUME:-veltos-build}"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

ensure_image() {
    if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
        cmd_image
    fi
}

cmd_image() {
    log "Building builder image $IMAGE"
    docker build -t "$IMAGE" "$HOST_ROOT/build/builder"
}

# Common docker run arguments: repo read-only at /src, outputs at /out.
run_builder() {
    mkdir -p "$REPO_ROOT/out"
    docker run --rm \
        -v "$HOST_ROOT:/src:ro" \
        -v "$HOST_ROOT/out:/out" \
        -e VELTOS_VERSION -e SOURCE_DATE_EPOCH \
        -e VELTOS_DEBIAN_MIRROR -e VELTOS_SECURITY_MIRROR \
        "$@"
}

source_date_epoch() {
    # Reproducible timestamps: the last commit time, if this is a git checkout.
    git -C "$REPO_ROOT" log -1 --format=%ct 2>/dev/null || date +%s
}

cmd_packages() {
    ensure_image
    run_builder "$IMAGE" bash /src/build/scripts/build-packages.sh /out/packages "$@"
}

cmd_iso() {
    ensure_image
    export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(source_date_epoch)}"
    log "Building ISO (SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH)"
    run_builder --privileged -v "$VOLUME:/build" "$IMAGE" \
        bash /src/build/scripts/build-iso.sh
}

ensure_kvm() {
    # Docker Desktop's VM ships kvm_intel/kvm_amd as modules that are not
    # loaded by default. Loading them is non-persistent (lost on restart).
    if docker run --rm --device /dev/kvm "$IMAGE" true >/dev/null 2>&1; then
        return 0
    fi
    log "/dev/kvm not available in containers; trying to load the KVM module in the Docker VM"
    docker run --rm --privileged --pid=host "$IMAGE" \
        nsenter -t 1 -m -- sh -c 'modprobe kvm_intel 2>/dev/null || modprobe kvm_amd' || true
    if ! docker run --rm --device /dev/kvm "$IMAGE" true >/dev/null 2>&1; then
        echo "error: KVM is not available; the boot test would be far too slow without it" >&2
        exit 1
    fi
}

cmd_test() {
    ensure_image
    ensure_kvm
    local mode="${1:-uefi}"
    local iso
    iso="$(ls -t "$REPO_ROOT"/out/iso/*/*.iso 2>/dev/null | head -n1 || true)"
    if [ -z "$iso" ]; then
        echo "error: no ISO under out/iso; run 'build/run.sh iso' first" >&2
        exit 1
    fi
    local rel="${iso#"$REPO_ROOT"/}"
    log "Boot test ($mode): $rel"
    run_builder --device /dev/kvm "$IMAGE" \
        python3 /src/tests/boot/vmtest.py --iso "/src/$rel" --firmware "$mode" \
        --results /out/test-results
}

cmd_test_winapps() {
    # Install a real Windows program (tests/boot/winapps-fixtures.json) in the
    # newest ISO through the VeltOS runner and check it lands in Start.
    ensure_image
    ensure_kvm
    local fixture="${1:-7zip}"
    local iso
    iso="$(ls -t "$REPO_ROOT"/out/iso/*/*.iso 2>/dev/null | head -n1 || true)"
    [ -n "$iso" ] || { echo "error: no ISO under out/iso" >&2; exit 1; }
    local rel="${iso#"$REPO_ROOT"/}"
    run_builder --device /dev/kvm "$IMAGE" python3 -c "
import json, subprocess, sys, urllib.request, hashlib, pathlib
f = json.load(open('/src/tests/boot/winapps-fixtures.json'))['$fixture']
cache = pathlib.Path('/out/cache/winapps'); cache.mkdir(parents=True, exist_ok=True)
exe = cache / f['file']
if not exe.exists() or hashlib.sha256(exe.read_bytes()).hexdigest() != f['sha256']:
    urllib.request.urlretrieve(f['url'], exe)
sys.exit(subprocess.call(['python3', '/src/tests/boot/winapps_vmtest.py', '--iso', '/src/$rel',
    '--exe', str(exe), '--sha256', f['sha256'], '--expect-shortcut', f['expect_shortcut'],
    '--results', '/out/test-results']))
"
}

cmd_preview() {
    # Development aid: install out/packages/*.deb into the newest live ISO in
    # a VM and screenshot a scripted interaction (see tests/boot/vmpreview.py).
    ensure_image
    ensure_kvm
    local iso
    iso="$(ls -t "$REPO_ROOT"/out/iso/*/*.iso 2>/dev/null | head -n1 || true)"
    [ -n "$iso" ] || { echo "error: no ISO under out/iso" >&2; exit 1; }
    local rel="${iso#"$REPO_ROOT"/}"
    run_builder --device /dev/kvm "$IMAGE" \
        python3 /src/tests/boot/vmpreview.py --iso "/src/$rel" --debs /out/packages \
        --results /out/preview ${1:+--actions "$1"}
}

cmd_vm() {
    # Long-running VM for step-by-step testing (see tests/boot/vmctl.py):
    #   build/run.sh vm start [cdrom|disk] [uefi|bios|secureboot]
    #   build/run.sh vm do "click:960,540 shot:name"   build/run.sh vm exec "cmd"
    #   build/run.sh vm stop        (screenshots: out/vm/, disk: volume veltos-vm)
    local action="${1:-}"
    shift || true
    case "$action" in
        start)
            ensure_image
            ensure_kvm
            docker rm -f veltos-vm >/dev/null 2>&1 || true
            local iso rel
            iso="$(ls -t "$REPO_ROOT"/out/iso/*/*.iso 2>/dev/null | head -n1 || true)"
            rel="${iso#"$REPO_ROOT"/}"
            mkdir -p "$REPO_ROOT/out/vm"
            docker run -d --name veltos-vm --device /dev/kvm                 -v "$HOST_ROOT:/src:ro" -v "$HOST_ROOT/out:/out" -v veltos-vm:/vm                 "$IMAGE" python3 /src/tests/boot/vmctl.py start --iso "/src/$rel"                 --disk /vm/disk.qcow2 --boot "${1:-cdrom}" --firmware "${2:-uefi}"                 --memory "${VELTOS_VM_MEMORY:-8192}" >/dev/null
            log "VM started (boot: ${1:-cdrom}, firmware: ${2:-uefi})"
            ;;
        do|exec|exec-user|upload|stop)
            docker exec veltos-vm python3 /src/tests/boot/vmctl.py "$action" "$@"
            ;;
        reset-disk)
            docker rm -f veltos-vm >/dev/null 2>&1 || true
            docker volume rm veltos-vm
            ;;
        *) echo "usage: build/run.sh vm start|do|exec|stop|reset-disk" >&2; exit 2 ;;
    esac
}

cmd_shell() {
    ensure_image
    run_builder -it --privileged -v "$VOLUME:/build" "$IMAGE" bash
}

cmd_clean() {
    log "Removing build volume $VOLUME"
    docker volume rm "$VOLUME"
}

main() {
    local cmd="${1:-}"
    shift || true
    case "$cmd" in
        image|packages|iso|test|preview|shell|clean) "cmd_$cmd" "$@" ;;
        test-winapps) cmd_test_winapps "$@" ;;
        vm) cmd_vm "$@" ;;
        *) sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 2 ;;
    esac
}

main "$@"
