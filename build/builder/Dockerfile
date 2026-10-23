# VeltOS build & test environment.
#
# Everything that builds or boots VeltOS runs in this container so the host
# (Windows, macOS or another Linux) is never modified. The base image is pinned
# by digest; bump it deliberately and record the change in docs/dev/development-log.md.
FROM debian:trixie@sha256:913f6706df59a68922d1dd08f78c2476560a8d367897200a6005b00e5f67c2d5

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates apt-utils \
      live-build debootstrap squashfs-tools xorriso mtools dosfstools \
      build-essential debhelper dpkg-dev fakeroot lintian \
      librsvg2-bin \
      qemu-system-x86 qemu-utils ovmf \
      python3 python3-pil \
      rsync git file procps \
      locales \
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
