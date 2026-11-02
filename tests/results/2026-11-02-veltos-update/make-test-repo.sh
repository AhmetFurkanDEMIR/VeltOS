#!/usr/bin/env bash
# A pretend "next release" for the VeltOS Update end-to-end test in the dev
# VM (2026-11-02), made in the builder container:
#
#   VELTOS_APT_SIGNING_KEY="$(cat out/keys/veltos-archive-private.asc)" \
#     docker run --rm -v "$PWD:/src:ro" -v "$PWD/out:/out" -e VELTOS_APT_SIGNING_KEY \
#     veltos-builder bash /out/vm/update-e2e/make-test-repo.sh SRC_DIR
#
# SRC_DIR: an ISO build's directory (its packages). On top of them: the new
# veltos-update, veltos-system and veltos-settings from out/packages, and
#  - veltos-base 1.1.0 (os-release says 1.1, as a release's would),
#  - veltos-calculator 1.1.0 (an app that changed),
#  - veltos-hello 1.1.0 (a new app, which veltos-system 1.1.0 pulls in),
# signed with VeltOS' archive key by build/scripts/make-apt-repo.sh like a
# release. Writes /out/vm/update-e2e/repo and release.json (the GitHub
# API's answer for that release).
set -euo pipefail

src="${1:?SRC_DIR}"
work=/out/vm/update-e2e
rm -rf "$work/debs" "$work/tmp" "$work/repo"
mkdir -p "$work/debs" "$work/tmp"
cp "$src"/*.deb "$work/debs/"
# An ISO build from before VeltOS Update lacks its packages: take them
# from out/packages then (an ISO build that has them keeps its own).
for pkg in veltos-update veltos-system veltos-settings; do
    if [ "$pkg" = veltos-settings ] || ! ls "$work/debs/${pkg}"_*.deb >/dev/null 2>&1; then
        if ! ls "$src/veltos-update"_*.deb >/dev/null 2>&1; then
            rm -f "$work/debs/${pkg}"_*.deb
            cp /out/packages/"${pkg}"_*.deb "$work/debs/"
        fi
    fi
done

md5() {
    (cd "$1" && find . -type f ! -path './DEBIAN/*' -printf '%P\0' | sort -z | xargs -0 -r md5sum > DEBIAN/md5sums)
}

# repack PACKAGE VERSION: unpack, set the version, let the caller change
# the tree ($dir), pack again.
unpack() {
    deb="$(ls "$work/debs/${1}"_*.deb)"
    dir="$work/tmp/$1"
    dpkg-deb -R "$deb" "$dir"
    sed -i "s/^Version: .*/Version: $2/" "$dir/DEBIAN/control"
    rm "$deb"
}
pack() {
    md5 "$dir"
    dpkg-deb --root-owner-group -Zxz -b "$dir" "$work/debs/${1}_${2}_all.deb" >/dev/null
}

unpack veltos-base 1.1.0
sed -i -e 's/^PRETTY_NAME=.*/PRETTY_NAME="VeltOS 1.1"/' -e 's/^VERSION_ID=.*/VERSION_ID="1.1"/' \
    -e 's/^VERSION=.*/VERSION="1.1"/' "$dir/usr/lib/os-release"
pack veltos-base 1.1.0

unpack veltos-calculator 1.1.0
pack veltos-calculator 1.1.0

unpack veltos-system 1.1.0
sed -i 's/^\(Depends: .*\)$/\1, veltos-hello/' "$dir/DEBIAN/control"
pack veltos-system 1.1.0

dir="$work/tmp/veltos-hello"
mkdir -p "$dir/DEBIAN" "$dir/usr/share/applications" "$dir/usr/share/doc/veltos-hello"
cat > "$dir/DEBIAN/control" <<'EOF'
Package: veltos-hello
Version: 1.1.0
Architecture: all
Maintainer: VeltOS Developers <veltos@example.invalid>
Section: misc
Priority: optional
Description: VeltOS Update test: a new app of the next release
 Only in the dev VM's pretend release (out/vm/update-e2e).
EOF
cat > "$dir/usr/share/applications/veltos-hello.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=VeltOS Hello (update test)
Exec=veltos-calculator
Icon=accessories-calculator
Categories=Utility;
EOF
echo "VeltOS Update test package." > "$dir/usr/share/doc/veltos-hello/README"
pack veltos-hello 1.1.0

VELTOS_VERSION=1.1 bash /src/build/scripts/make-apt-repo.sh "$work/debs" "$work/repo"

iso_name=VeltOS-1.1-amd64.iso
python3 - "$work" "$iso_name" <<'EOF'
import json, subprocess, sys
from pathlib import Path
work, iso = Path(sys.argv[1]), sys.argv[2]
body = subprocess.run(["python3", "/src/build/scripts/release-notes.py", "1.1", iso, "0" * 64],
                      capture_output=True, text=True, check=True).stdout
release = {
    "tag_name": "v1.1", "name": "VeltOS 1.1", "body": body,
    "published_at": "2026-11-02T12:00:00Z",
    "html_url": "https://github.com/AhmetFurkanDEMIR/VeltOS/releases/tag/v1.1",
    "assets": [{"name": iso, "size": 2093000000,
                "browser_download_url": f"https://github.com/AhmetFurkanDEMIR/VeltOS/releases/download/v1.1/{iso}"}],
}
(work / "release.json").write_text(json.dumps(release, indent=1), encoding="utf-8")
print("release.json:", len(body), "characters of notes")
EOF
ls "$work/repo" | head -50
