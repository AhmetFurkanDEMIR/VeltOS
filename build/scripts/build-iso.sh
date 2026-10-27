#!/usr/bin/env bash
# Build the VeltOS live ISO with live-build (inside the privileged builder
# container). Expects the repo at /src (read-only), a persistent build volume
# at /build and the output directory at /out.
set -euo pipefail

VELTOS_VERSION="${VELTOS_VERSION:-1.0}"
export VELTOS_VERSION
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(date +%s)}"

LB_DIR=/build/live-build
STAMP="$(date -u -d "@$SOURCE_DATE_EPOCH" +%Y%m%d-%H%M%S)"
RESULT_DIR="/out/iso/veltos-${VELTOS_VERSION}-${STAMP}"

echo "==> Building VeltOS packages"
bash /src/build/scripts/build-packages.sh /build/packages

echo "==> Preparing live-build tree in $LB_DIR"
if [ -d "$LB_DIR/config" ]; then
    (cd "$LB_DIR" && lb clean noauto)
fi
mkdir -p "$LB_DIR"
# Keep the package cache between builds; everything else comes from /src.
find "$LB_DIR" -mindepth 1 -maxdepth 1 ! -name cache -exec rm -rf {} +
cp -a /src/build/live-build/. "$LB_DIR"/
# Normalise modes (Windows bind mounts mark every file executable).
find "$LB_DIR/auto" "$LB_DIR/config" -type f -exec chmod 644 {} +
chmod 755 "$LB_DIR"/auto/* "$LB_DIR"/config/hooks/*/*
mkdir -p "$LB_DIR/config/packages.chroot"
cp /build/packages/*.deb "$LB_DIR/config/packages.chroot/"

# The image build, shown as "OS build" in Settings > About.
mkdir -p "$LB_DIR/config/includes.chroot_after_packages/usr/lib/veltos"
printf 'VELTOS_BUILD=%s\n' "$(date -u -d "@$SOURCE_DATE_EPOCH" +%Y%m%d.%H%M)" \
    > "$LB_DIR/config/includes.chroot_after_packages/usr/lib/veltos/build-info"

# The live boot menu uses veltos-boot's GRUB fonts (Inter) and selection
# highlight, so they are generated in one place only.
boot_tmp="$(mktemp -d)"
dpkg-deb -x /build/packages/veltos-boot_*.deb "$boot_tmp"
cp "$boot_tmp"/usr/share/grub/themes/veltos/inter-*.pf2 \
   "$boot_tmp"/usr/share/grub/themes/veltos/select_*.png \
   "$LB_DIR/config/bootloaders/grub-pc/live-theme/"
rm -rf "$boot_tmp"

cd "$LB_DIR"
lb config
echo "==> lb build (log: $RESULT_DIR/build.log)"
mkdir -p "$RESULT_DIR"
# 1 MiB squashfs blocks (live-build's default is 128 KiB) and xz with the
# x86 filter for programs (auto/config): the ISO must stay under 2 GiB, the
# most a GitHub release file may have, without leaving anything out. On the
# ISO of 2026-10-26 (6.0 GB of files) zstd level 19 made 2155.9 MB, zstd 22
# 2155.4 MB and xz with -Xbcj x86 1985.3 MB; xz unpacks more slowly (all
# files: 18 s instead of 7 s), which only the live system and the
# installer's copy feel, not the installed system. live-build adds
# MKSQUASHFS_OPTIONS after its "-comp xz".
export MKSQUASHFS_OPTIONS="-b 1M -Xbcj x86"
set +e
lb build 2>&1 | tee "$RESULT_DIR/build.log"
status=${PIPESTATUS[0]}
set -e
if [ "$status" -ne 0 ]; then
    echo "error: lb build failed with status $status" >&2
    exit "$status"
fi

iso="$(ls ./*.iso)"
# Every ISO is published as a GitHub release file, which must stay under
# 2 GiB (docs.github.com, "About releases"; product owner, 2026-10-27:
# "the ISO must always stay under 2 GB"). A larger one fails the build.
ISO_LIMIT=2147483648
iso_size="$(stat -c %s "$iso")"
if [ "$iso_size" -ge "$ISO_LIMIT" ]; then
    echo "error: $(basename "$iso") is $iso_size bytes; a GitHub release file must stay under $ISO_LIMIT" >&2
    cp "$iso" "$RESULT_DIR/" 2>/dev/null || true
    exit 3
fi
echo "==> ISO size: $iso_size bytes ($(( (ISO_LIMIT - iso_size) / 1048576 )) MiB under the 2 GiB limit)"
cp "$iso" "$RESULT_DIR/"
cp ./*.packages "$RESULT_DIR/" 2>/dev/null || true
cp ./*.contents "$RESULT_DIR/" 2>/dev/null || true
cp /build/packages/*.deb "$RESULT_DIR/"
(cd "$RESULT_DIR" && sha256sum ./*.iso > SHA256SUMS)
cat > "$RESULT_DIR/build-info.txt" <<EOF
veltos_version: $VELTOS_VERSION
source_date_epoch: $SOURCE_DATE_EPOCH
built_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)
iso: $(basename "$iso")
iso_size_bytes: $(stat -c %s "$iso")
builder_tools:
$(sed 's/^/  /' /etc/veltos-builder-versions)
EOF
echo "==> Done: $RESULT_DIR"
ls -l "$RESULT_DIR"
