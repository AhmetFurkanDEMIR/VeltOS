# Testing

VeltOS treats test evidence as part of the product: a feature is "done"
only with a test that shows it working, and results are reported as
observed — including failures.

## Test layers (current)

| Layer | Where | Runs when | What it proves |
|---|---|---|---|
| Package unit tests | `packages/*/tests/` | Every package build (`dh_auto_test`) | Asset generation, colour derivation, os-release, layout script structure |
| Build-time invariants | `build/live-build/config/hooks/normal/9000-veltos-verify.hook.chroot` | Every ISO build, inside the chroot | VeltOS packages installed, os-release diverted, Debian branding absent, global theme selected |
| VM boot test | `tests/boot/vmtest.py` (`build/run.sh test [bios\|uefi\|secureboot]`) | On demand after an ISO build | ISO boots, live session reaches a Plasma desktop with VeltOS layout/branding; collects measurements |

## VM boot test details

- QEMU/KVM, q35 machine, host CPU model, 4 vCPU, 4096 MiB RAM,
  `virtio-vga` at 1920x1080 **without 3D acceleration** (Plasma renders with
  Mesa llvmpipe in this setup — slower than real hardware and not
  representative of GPU performance).
- Firmware modes: `bios` (SeaBIOS), `uefi` (OVMF), `secureboot` (OVMF with
  Microsoft keys; exercises Debian's signed shim → GRUB → kernel chain).
- Flow: the boot menu is hidden like on Windows, so the test presses F4
  3 s after start to reveal it, screenshots it, presses Enter, screenshots
  the boot splash, waits for the guest agent, then polls until
  `plasmashell` runs for the live user, idles for 60 s, screenshots the
  desktop (with the live welcome window), checks the live experience
  (Plymouth theme in the initramfs, welcome window, application names,
  per-user defaults), closes the welcome window, screenshots the clean
  desktop and the Start menu, and records measurements.
- Required checks fail the run (exit code 1). Advisory checks are reported
  as WARN (e.g. degraded systemd state, X11 instead of Wayland).

### Measurement caveats

Numbers from the boot test describe **a live session in a VM**:

- Idle RAM is `MemTotal - MemAvailable` after 60 s idle. In a live session
  the root filesystem is a SquashFS + tmpfs overlay; files written at
  runtime live in RAM (reported separately as Shmem). An installed system
  will differ; the 1–1.5 GB idle target must be judged on an installed
  system with the methodology recorded next to the number.
- "Boot time" is `systemd-analyze` inside the guest (firmware + loader +
  kernel + userspace as seen by systemd) plus the wall-clock times the
  harness records (`guest_agent_ready_s`, `plasmashell_running_s`, measured
  from QEMU start and including the deliberate boot-menu delay).
- llvmpipe rendering inflates CPU use and plasmashell/kwin memory.

## Result records

- Raw results: `out/test-results/<UTC stamp>-<firmware>/` (not committed).
- Milestone evidence: copied to `tests/results/<milestone>/` and summarised
  in `docs/status.md`.

## Not covered yet (planned)

- Installation into a disposable VM disk through Calamares (Milestone 5).
- Desktop interaction tests (launcher, keyboard navigation, scaling).
- Real hardware matrix: NVIDIA, AMD, Intel GPUs; Wi-Fi/Bluetooth/audio.
  The template lives in `docs/hardware-support.md` once Milestone 2 starts.
- Windows application and game compatibility (Milestones 3–4).
- Upgrade and recovery tests (Milestone 5).
- CI automation of all of the above.
