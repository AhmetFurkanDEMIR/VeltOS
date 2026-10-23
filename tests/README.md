# tests/

| Path | What |
|---|---|
| `boot/vmtest.py` | Boots an ISO in QEMU/KVM (UEFI, BIOS or Secure Boot), checks the live desktop through QMP and the QEMU guest agent, and records screenshots and measurements (start-up times, memory, crashes). Run with `build/run.sh test [uefi\|bios\|secureboot]`. |
| `boot/winapps_vmtest.py` | Installs a real Windows program (a pinned 7-Zip installer, `boot/winapps-fixtures.json`) through `veltos-run` in a VM and checks that it lands in Start. Run with `build/run.sh test-winapps`. |
| `boot/vmpreview.py` | Development aid: installs freshly built `.deb` files into a live VM and screenshots a scripted interaction. Run with `build/run.sh preview`. |
| `boot/vmctl.py` | A long-running VM driven step by step (installations, demos, screenshots). Run with `build/run.sh vm start\|do\|exec\|exec-user\|upload\|stop`. |
| `boot/vmlib.py` | QEMU, QMP and guest-agent helpers shared by the scripts above. |
| `repo/` | Repository-wide checks, run by every package build: line endings, control characters, the logo's copies, the website's icons, Qt keyword arguments that break in a Turkish locale. |
| `results/` | Committed evidence of milestone test runs: reports and screenshots. |

Package unit tests live next to the packages (`packages/*/tests/`) and run
during every package build.

Methodology, measurements and their limits (software rendering in VMs,
VirtualBox in NEM mode), and what is not covered yet:
[docs/dev/testing.md](../docs/dev/testing.md).
