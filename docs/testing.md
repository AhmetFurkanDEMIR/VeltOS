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

## Checks in VirtualBox (the product owner's set-up)

The ISO can be booted headless in a throw-away VirtualBox VM on the
developer host with the scripts in `out/vbox/` (`boot-probe.sh NAME [ISO]
[VRAM]`, `boot-probe2.sh NAME CONTROLLER 3D [VRAM]`, `diag-probe.sh` for a
journal dump over a serial port). They mirror the product owner's VM
(BIOS, PIIX3, VMSVGA, 3D off) and keep their own VMs under
`out/vbox/vms`. See AGENTS.md for the VBoxManage calls.

When the desktop comes late or stays black there (2026-10-22):

- First compare the QEMU boot-test reports across ISOs
  (`out/test-results/*/report.md`, "plasmashell running for live user |
  after N s"): a jump between two ISOs points at that ISO's changes, not
  at VirtualBox. The session-start deadlock of the portal platform theme
  showed as 18 s → 95 s on QEMU too.
- In the VM, on tty2 (Ctrl+Alt+F2; the live user is logged in there):
  `systemd-analyze --user critical-chain plasma-workspace.target`,
  `systemd-analyze --user blame | head`, and `journalctl -b -o
  short-monotonic | grep -iE 'WaitForName|timed out|Failed to start'`
  name the unit that waits and the D-Bus service it waits for.
- To try a changed session environment, edit
  `/etc/xdg/plasma-workspace/env/veltos-session.sh` itself (`sudo sed
  -i`) — a later `99-*.sh` file is sourced *before* it and cannot unset
  its exports — then `sudo systemctl restart sddm`. After the restart send
  no VT keystrokes (SDDM activates its VT itself) and force real repaints
  (Start, Win+Tab) before trusting a screenshot: VirtualBox's framebuffer
  keeps the last text console when a compositor never paints.
  Screenshot sizes tell the state at a glance: ~3.5 KB black, ~11.5 KB a
  text console, 100 KB and more a painted desktop.
- The sign-in screen is not seen on the live ISO (automatic login): write
  `/etc/sddm.conf.d/zz-noautologin.conf` with `[Autologin]`, `User=` and
  `Session=` empty, restart SDDM, and the greeter appears.

## Manual checks in the long-running VM (`build/run.sh vm`)

Patterns that worked on 2026-10-21 (see `tests/boot/vmctl.py`):

- Install rebuilt packages: `build/run.sh vm upload /tmp /out/packages/X.deb`
  then `build/run.sh vm exec "dpkg -i /tmp/X.deb"`; after Plasma packages
  delete `~/.cache/plasmashell/qmlcache` and restart
  `plasma-plasmashell.service` (`systemctl --user -M velt@.host restart ...`).
- Programs that need the *login session* (polkit prompts, PackageKit):
  `systemd-run --machine=velt@.host --user --collect --unit=NAME sh -c '...'`;
  `vm exec-user` runs outside any session and polkit finds no agent there.
  The live `sudo_on_live.rules` grants everything without a prompt: move
  it out of `/usr/share/polkit-1/rules.d/` to see the prompt, and put it back.
- Session environment for a test (e.g. `QT_QPA_PLATFORMTHEME`):
  `systemctl --user -M velt@.host set-environment NAME=value`, then start
  the program with `systemd-run ... --user`.
- The sign-in screen: move `/etc/sddm.conf` (live-config's autologin,
  which overrides every `sddm.conf.d` file) aside, `systemctl restart
  sddm`, screenshot, type the password (`echo velt:pw | chpasswd` first),
  then put the file back. The session restarts; redo any set-environment.
- Keys for `vm do`: QEMU qcodes (`esc`, `ret`, `ctrl+o`, `meta_l`); `type:`
  for text.

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
