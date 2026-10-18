# Shared by the VeltOS installer jobs (sourced, not executed).
# Based on calamares-settings-debian helpers (ISC licence, Jonathan Carter).

# Calamares mounts the target system at /tmp/calamares-root-XXXXXXXX.
target_root() {
    findmnt -rn -o TARGET | grep -E '^/tmp/calamares-root-[^/]+$' | head -n 1
}

CHROOT="$(target_root)"
if [ -z "$CHROOT" ] || [ ! -d "$CHROOT" ]; then
    echo "veltos-installer: target root not found" >&2
    exit 1
fi

in_target() {
    DEBIAN_FRONTEND=noninteractive chroot "$CHROOT" "$@"
}
