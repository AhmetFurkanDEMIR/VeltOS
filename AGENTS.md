# AGENTS.md — Working on VeltOS

This file is for AI coding agents and new human contributors. It contains
the project rules, where things are, and how to continue the work. Read it
fully before changing anything, then read `docs/status.md` (what is done)
and `docs/architecture.md` (why it is built this way).

## Project in one paragraph

VeltOS ("Your PC. No Limits.") is a Debian 13 "trixie" based desktop
distribution with a Windows 11-inspired KDE Plasma desktop, hardware-aware
driver management and (planned) strong Windows application and game
compatibility through Wine/Proton. It is built incrementally as a real,
installable OS with reproducible builds and automated tests. The product
owner sets priorities; agents act as the engineering team.

## Rules (non-negotiable)

1. **Language.** Everything in the repository is English: code, comments,
   docs, commit messages, package descriptions. (The product owner may talk
   to agents in Turkish; answer in the language you are addressed in, but
   write the repo in English.)
2. **Working software first.** A bootable, installable system beats
   ambitious unimplemented features. Work in small, verifiable increments.
3. **Never fabricate results.** Do not claim a build passed, a test ran,
   hardware works or a feature is complete unless you observed it. Report
   failures with their output. Mark anything untested as untested.
4. **No silent mocks.** Never replace a real implementation with a mock or
   stub without labelling it clearly in code and in `docs/status.md`.
5. **Reuse, don't rewrite.** Use Debian, KDE, Mesa, Wine/Proton and other
   mature upstream components. VeltOS code goes into small, testable
   packages under `packages/`. Do not fork Plasma, the kernel or Wine.
6. **Verify upstream facts.** Check package names/versions against
   packages.debian.org or `apt-cache policy` in the builder container and
   read upstream docs; do not rely on memory. Record what you verified.
7. **Lightweight by default.** Every new service, daemon or autostart
   entry needs a reason; measure RAM/CPU/boot impact (see `docs/testing.md`).
8. **Security and safety.** Packages come only from signed Debian archives
   or are built from this repo. Never install drivers from unverified
   downloads. Never run untrusted `.exe` files with elevated privileges.
   Wine is not a sandbox — say so.
9. **Host safety.** Never repartition disks, change boot configuration,
   overwrite user data or run destructive commands on a developer's machine
   without explicit approval. Builds and tests run in the builder container.
10. **Honest claims.** Never promise universal Windows compatibility or
    "native performance" without comparative measurements.
11. **Explain decisions.** Architectural choices go into
    `docs/architecture.md` with alternatives and trade-offs.
12. **Keep the handoff current.** After any meaningful change update
    `docs/status.md`, add an entry to `docs/development-log.md`, and keep
    README files accurate. The next agent must be able to continue from the
    repository alone.

## Repository map

| Path | What |
|---|---|
| `build/run.sh` | Single entry point: `image`, `packages`, `iso`, `test`, `shell`, `clean` |
| `build/builder/Dockerfile` | Build/test container (Debian trixie, pinned by digest) |
| `build/scripts/` | In-container scripts: package build, ISO build |
| `build/live-build/` | live-build config: `auto/config` (options), package lists, APT pins, hooks, GRUB menu/theme, boot splash |
| `packages/veltos-base/` | VeltOS `os-release` identity (dpkg diversion) |
| `packages/veltos-desktop/` | Plasma themes (Light default), Windows 11 style taskbar + VeltOS Start menu, colour schemes, generated wallpaper, splash, login/lock screen, master logo |
| `packages/veltos-fluent-icons/` | Fluent icons/cursors from a pinned upstream release (Microsoft logos removed) |
| `packages/veltos-boot/` | Plymouth splash, GRUB theme, boot defaults |
| `packages/calamares-settings-veltos/` | VeltOS installer (Calamares) configuration and branding |
| `packages/veltos-winapps/` | `veltos-run`: double-click `.exe`/`.msi` → install/open via Wine |
| `packages/veltos-wine-addons/` | Wine Mono/Gecko (pinned, verified) |
| `tests/boot/vmlib.py` | Shared QEMU/QMP/guest-agent helpers |
| `tests/boot/vmtest.py` | QEMU/KVM boot test with screenshots, checks and measurements (`build/run.sh test`) |
| `tests/boot/vmpreview.py` | Dev aid: install fresh `.deb`s into a live VM and screenshot a scripted interaction (`build/run.sh preview`) |
| `tests/boot/winapps_vmtest.py` | Installs a real Windows program through `veltos-run` in a VM (`build/run.sh test-winapps`) |
| `tests/repo/` | Repository-wide checks (logo copies, line endings) |
| `tests/results/` | Committed test evidence for milestones |
| `docs/` | Architecture, build guide, testing, status, development log |
| `out/` | Build outputs (ISO, logs, test runs) — git-ignored |

## How to continue

1. Read `docs/status.md`; pick the first item under "Next steps" unless the
   product owner says otherwise.
2. Make sure the environment works: `build/run.sh packages` (fast) and, for
   image changes, `build/run.sh iso` followed by `build/run.sh test`.
3. Change the smallest thing that delivers the step. Add or update tests.
4. Build and test for real. Read the report (`out/test-results/.../report.md`)
   and look at the screenshots.
5. Update `docs/status.md`, `docs/development-log.md`, README files and,
   for design decisions, `docs/architecture.md`.
6. Commit with a clear English message describing what changed and what was
   verified.

## Conventions

- Debian packaging: debhelper compat 13, `3.0 (native)`, one package per
  directory in `packages/`, version `X.Y.Z~devN` during development. Put
  generated files in `build-assets/` (git-ignored) via `debian/rules`.
- Package unit tests: Python `unittest` under `packages/<pkg>/tests/`, run
  by `override_dh_auto_test`. Standard library only.
- Shell: `bash` with `set -euo pipefail` for scripts; POSIX `sh` for
  live-build hooks and maintainer scripts.
- Line endings: LF everywhere (`.gitattributes`). Files from a Windows bind
  mount appear executable in containers; build scripts normalise modes.
- Artwork: SVG sources in the package; PNGs are rendered at build time.
  Brand palette: blue `#4F7CFF`, indigo `#5B3FE0`, cyan `#2FA8F0`,
  navy background `#050818`–`#0E1846`.
- Naming: packages `veltos-*`; Plasma IDs `org.veltos.*`; live user `velt`.

## Gotchas learned so far

- `/dev/kvm` is missing in Docker Desktop containers until the KVM module
  is loaded in Docker's VM; `build/run.sh test` handles it.
- live-build's GRUB template has no timeout; ours sets 10 s.
- live-build substitutes placeholders in `config/bootloaders/grub-pc/grub.cfg`
  with unanchored `sed` (e.g. any `KERNEL_LIVE`, `APPEND_LIVE`, `MEMTEST`
  text is replaced) — avoid those words in comments there.
- debhelper treats executable `debian/*.install` files as dh-exec scripts.
- live-build turns `/etc/os-release` into a *copy* of Debian's file
  (`bootstrap_debootstrap`), so diverting `/usr/lib/os-release` alone is not
  enough; hook `8000-veltos-os-release` restores the symlink. Always check
  identity in the booted system, not only in the build chroot.
- live-build's `--firmware-chroot true` also installs contrib
  `firmware-b43*-installer` packages that download non-redistributable
  firmware during the build. VeltOS uses an explicit firmware list
  (`veltos-firmware.list.chroot`); the verify hook rejects the installers.
- `*.list.binary` package lists need `apt-utils` (apt-ftparchive) in the
  builder image.
- Foreign-architecture packages (`wine32:i386`) in a `.list.chroot` make
  live-build enable that architecture automatically.
- On Windows, Python's `Path.write_text()` writes CRLF; make writes break.
  Write bytes or use `newline="\n"`. `build-packages.sh` refuses CRLF
  files and `tests/repo` checks the whole tree.
- debhelper runs `dh_auto_test` *before* `dh_auto_install`; checks on the
  installed tree belong in `execute_after_dh_auto_install`. `python3 -m
  unittest` with zero tests exits non-zero (good: catches missing tests).
- Debian version ordering: `10.0~repack-6` is *lower* than `10.0`. Use
  `(>= 10.0~)` in dependencies.
- Plasma 6.3 `Kicker.SystemModel` dereferences its favorites model
  without a null check: create it only after `RootModel.refresh()` (see
  `StartMenu.qml`). Found by `coredumpctl` in the VM; boot tests now fail
  on any core dump.
- Fluent icons draw `start-here*` and Wine icons as Microsoft's Windows
  logo; `veltos-fluent-icons` replaces/removes them. Re-check after
  updating upstream.
- Debian's Wine does not download Wine Mono/Gecko; `veltos-wine-addons`
  ships the exact versions Wine expects (see `dlls/appwiz.cpl/addons.c`).
- Plasma applies the global theme's layout script only to users without
  existing Plasma configuration.
