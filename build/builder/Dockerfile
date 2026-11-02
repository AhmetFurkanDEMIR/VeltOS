# VeltOS build & test environment.
#
# Everything that builds or boots VeltOS runs in this container so the host
# (Windows, macOS or another Linux) is never modified. The base image is pinned
# by digest; bump it deliberately and record the change in docs/dev/development-log.md.
FROM debian:trixie@sha256:913f6706df59a68922d1dd08f78c2476560a8d367897200a6005b00e5f67c2d5

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8

# Other Debian mirrors for this build only (build/run.sh image passes
# VELTOS_DEBIAN_MIRROR / VELTOS_SECURITY_MIRROR, as for the package builds):
# a slow CDN, or a snapshot while the host's clock is behind. The image
# keeps deb.debian.org.
ARG VELTOS_DEBIAN_MIRROR=
ARG VELTOS_SECURITY_MIRROR=
RUN cp /etc/apt/sources.list.d/debian.sources /tmp/debian.sources \
 && if [ -n "$VELTOS_DEBIAN_MIRROR" ]; then sed -i "s|^URIs: http://deb.debian.org/debian$|URIs: ${VELTOS_DEBIAN_MIRROR%/}|" /etc/apt/sources.list.d/debian.sources; fi \
 && if [ -n "$VELTOS_SECURITY_MIRROR" ]; then sed -i "s|^URIs: http://deb.debian.org/debian-security$|URIs: ${VELTOS_SECURITY_MIRROR%/}|" /etc/apt/sources.list.d/debian.sources; fi \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates apt-utils gpg gpg-agent \
      live-build debootstrap squashfs-tools xorriso mtools dosfstools \
      build-essential debhelper dpkg-dev fakeroot lintian \
      librsvg2-bin \
      qemu-system-x86 qemu-utils ovmf \
      python3 python3-pil \
      rsync git file procps \
      zstd \
      locales \
 && mv /tmp/debian.sources /etc/apt/sources.list.d/debian.sources \
 && rm -rf /var/lib/apt/lists/*

# Turkish locale for the package tests: Turkish case rules (dotted and
# dotless i) broke File Explorer on Turkish systems while every test in a
# C/English locale passed (2026-10-20).
RUN sed -i 's/^# *\(tr_TR.UTF-8 UTF-8\)/\1/' /etc/locale.gen && locale-gen

# Record exact tool versions in the image for build provenance.
RUN dpkg-query -W -f='${Package} ${Version}\n' \
      live-build debootstrap qemu-system-x86 ovmf debhelper \
      > /etc/veltos-builder-versions

WORKDIR /work
