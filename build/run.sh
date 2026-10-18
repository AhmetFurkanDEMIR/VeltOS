#!/usr/bin/env bash
# VeltOS developer entry point. Every step runs inside the veltos-builder
# container, so the host only needs Docker (Linux, macOS, or Windows with
# Docker Desktop + Git Bash). See docs/build-guide.md.
#
#   build/run.sh image        build the builder container image
#   build/run.sh packages     build the VeltOS .deb packages into out/packages
#   build/run.sh iso          build packages + the live ISO into out/iso
#   build/run.sh test [mode]  boot the newest ISO in QEMU/KVM and verify it
#                             (mode: uefi (default), bios, secureboot)
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
    run_builder "$IMAGE" bash /src/build/scripts/build-packages.sh /out/packages
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
        image|packages|iso|test|shell|clean) "cmd_$cmd" "$@" ;;
        *) sed -n '2,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 2 ;;
    esac
}

main "$@"
