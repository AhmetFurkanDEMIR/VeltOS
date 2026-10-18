# tests/

| Path | What |
|---|---|
| `boot/vmtest.py` | Boots an ISO in QEMU/KVM (BIOS, UEFI or Secure Boot), verifies the live desktop through QMP and the QEMU guest agent, records screenshots and measurements. Run with `build/run.sh test [bios\|uefi\|secureboot]`. |
| `results/` | Committed evidence from milestone test runs (reports + screenshots). |

Package unit tests live next to the packages (`packages/*/tests/`) and run
during every package build.

Methodology, caveats and what is not covered yet:
[docs/testing.md](../docs/testing.md).
