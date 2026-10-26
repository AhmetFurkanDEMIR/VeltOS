# File Explorer drive formatting and icons

Item 42 of the product owner's list.

## Verified

- `veltos-explorer`, `veltos-disks` and `veltos-fluent-icons` built
  successfully after 8 repository checks, 80 Explorer tests, 21 Disk
  Management tests and 2 icon-package tests passed.
- The rebuilt packages were installed in the live QEMU development VM.
  A 1 GiB `scsi_debug` removable disk, backed only by the VM's synthetic
  SCSI device, was used as the safe test volume. No physical storage was
  used.
- This PC showed the removable-disk icon separately from the framed
  Windows icons on fixed NTFS volumes. The synthetic USB-transport icon
  is covered by the Explorer classification tests and the icon-package
  build checks.
- Right-clicking the test volume showed **Format...** and opened Disk
  Management's Format form. Clicking OK opened the second data-loss
  warning; **No** cancelled it. The ext4 UUID stayed
  `046f73df-e2c0-41eb-926d-69460de33c8a`, confirming no format ran.
- Right-clicking the live system volume showed Open and Properties only;
  it did not offer Format.

## Screenshots

- `format-this-pc.png` — removable test volume and fixed NTFS drives with
  their distinct icons.
- `format-drive-menu.png` — the removable volume's Format command.
- `format-dialog.png` — the Windows-style Format form.
- `format-confirmation.png` — the separate data-loss warning.
- `format-cancelled.png` — Disk Management after choosing No.
- `format-system-drive-menu.png` — the live system volume without Format.
