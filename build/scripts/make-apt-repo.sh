#!/usr/bin/env bash
# VeltOS' package repository for VeltOS Update: a flat APT repository whose
# files become assets of a GitHub release, so installed PCs read it at
# https://github.com/AhmetFurkanDEMIR/VeltOS/releases/latest/download/
# (veltos-update's veltos.sources).
#
#   make-apt-repo.sh DEBS_DIR OUT_DIR
#
# DEBS_DIR holds the ISO build's own packages (build-iso.sh copies them next
# to the ISO), so the ISO and the updates carry the same builds. Every file
# gets a name GitHub keeps as it is (it renames assets with characters such
# as "~" or "+"): the index names the renamed files. With
# VELTOS_APT_SIGNING_KEY (an ASCII-armoured secret key, a GitHub Actions
# secret) the index is signed (InRelease, Release.gpg); without it the
# repository is left unsigned and the script says so.
set -euo pipefail

debs="${1:?DEBS_DIR}"
out="${2:?OUT_DIR}"
rm -rf "$out"
mkdir -p "$out"

count=0
for deb in "$debs"/*.deb; do
    name="$(basename "$deb")"
    safe="$(printf '%s' "$name" | sed 's/[^A-Za-z0-9._-]/-/g')"
    cp "$deb" "$out/$safe"
    count=$((count + 1))
done
[ "$count" -gt 0 ] || { echo "error: no .deb files in $debs" >&2; exit 1; }

cd "$out"
apt-ftparchive packages . > Packages
xz -9 -k Packages
gzip -9 -n -k Packages
apt-ftparchive \
    -o APT::FTPArchive::Release::Origin=VeltOS \
    -o APT::FTPArchive::Release::Label=VeltOS \
    -o APT::FTPArchive::Release::Suite=stable \
    -o "APT::FTPArchive::Release::Version=${VELTOS_VERSION:-}" \
    -o APT::FTPArchive::Release::Architectures="amd64 all" \
    -o "APT::FTPArchive::Release::Description=VeltOS' own packages (VeltOS Update)" \
    release . > Release

if [ -n "${VELTOS_APT_SIGNING_KEY:-}" ]; then
    GNUPGHOME="$(mktemp -d)"
    export GNUPGHOME
    printf '%s\n' "$VELTOS_APT_SIGNING_KEY" | gpg --batch --quiet --import
    gpg --batch --yes --pinentry-mode loopback --passphrase "" --clearsign -o InRelease Release
    gpg --batch --yes --pinentry-mode loopback --passphrase "" --armor --detach-sign -o Release.gpg Release
    gpg --batch --armor --export > veltos-archive-keyring.asc
    gpg --batch --verify InRelease 2>&1 | sed 's/^/  /'
    rm -rf "$GNUPGHOME"
else
    echo "warning: VELTOS_APT_SIGNING_KEY is not set: the repository is not signed" >&2
fi
echo "$count packages in $out"
