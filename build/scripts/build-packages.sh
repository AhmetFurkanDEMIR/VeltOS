#!/usr/bin/env bash
# Build every VeltOS Debian package under /src/packages (inside the builder
# container). Usage: build-packages.sh OUTPUT_DIR
set -euo pipefail

OUT="${1:?usage: build-packages.sh OUTPUT_DIR}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$OUT"
rm -f "$OUT"/*.deb "$OUT"/*.buildinfo "$OUT"/*.changes

echo "==> Repository consistency tests"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s /src/tests/repo -v

apt_updated=false
for src in /src/packages/*/; do
    name="$(basename "$src")"
    echo "==> Building package source $name"
    # Copy without generated artefacts; the repo mount is read-only.
    mkdir -p "$WORK/$name"
    tar -C "$src" --exclude=build-assets --exclude=__pycache__ -cf - . | tar -C "$WORK/$name" -xf -
    # Bind mounts from Windows report every file as executable, and debhelper
    # runs executable *.install files as dh-exec scripts. Normalise modes.
    # CRLF line endings (e.g. from Windows editors) break make and shell.
    if crlf="$(grep -rlI $'\r' "$WORK/$name")"; then
        echo "error: CRLF line endings in:" >&2
        echo "$crlf" >&2
        exit 1
    fi
    find "$WORK/$name" -type d -exec chmod 755 {} +
    find "$WORK/$name" -type f -exec chmod 644 {} +
    chmod 755 "$WORK/$name/debian/rules"

    # Packages of third-party artwork pin an upstream release (upstream.json);
    # it is downloaded, checksum-verified and unpacked into upstream/.
    if [ -f "$WORK/$name/upstream.json" ]; then
        python3 /src/build/scripts/fetch-upstream.py "$WORK/$name" "$WORK/$name/upstream"
    fi

    cd "$WORK/$name"
    # e.g. "dpkg-checkbuilddeps: error: unmet build dependencies: foo (>= 1) | bar baz:native"
    missing="$(dpkg-checkbuilddeps 2>&1 | sed -n 's/.*[Uu]nmet build dependencies: //p' \
               | sed -E 's/\([^)]*\)//g; s/\|[^ ]*//g; s/:native//g' || true)"
    if [ -n "$missing" ]; then
        if [ "$apt_updated" = false ]; then
            apt-get update -qq
            apt_updated=true
        fi
        # shellcheck disable=SC2086
        DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends $missing
    fi

    dpkg-buildpackage --build=binary --no-sign
    # Lintian findings are reported but do not fail the build yet.
    lintian --info --display-info ../"${name}"_*.changes || true
done

mv "$WORK"/*.deb "$OUT"/
echo "==> Packages in $OUT:"
ls -l "$OUT"
