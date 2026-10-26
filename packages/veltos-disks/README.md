# veltos-disks — VeltOS Disk Management

Windows 11's Disk Management, as a VeltOS app (PySide6/QML) on UDisks2:

- the **volume list** on top (Volume, Layout, Type, File System, Status,
  Capacity, Free Space, % Free) and the **disk map** below: every disk
  ("Disk 0", "Disk 1", "CD-ROM 0") with its header box (kind, size,
  Online / No Media / Not Initialized) and its partitions and unallocated
  space drawn to scale, with Disk Management's coloured stripes (primary
  navy, logical blue, free space green, unallocated black hatching);
- the right-click menu of a volume: Open / Explore (File Explorer at the
  mount point; a volume that is not mounted is mounted first), Mount /
  Unmount, Eject, Change Volume Label…, Format…, Delete Volume…,
  Properties; of unallocated space: New Simple Volume…; of a blank disk:
  Initialize Disk… (GPT or MBR);
- dialogs in the Windows 11 layout (`qml/FormDialog.qml`): New Simple Volume (size in MB up to the free space, file system, label),
  Delete, label, Initialize, Properties and errors.
- **Format** has its own window in Windows 11's layout
  (`qml/FormatWindow.qml`, 2026-10-26): capacity, file system, volume
  label, Quick Format, Start; the data-loss question inside the window,
  then a progress bar while UDisks2 formats and "Format complete" (or
  the error) at the end.
- `veltos-disks --format /dev/sdb1` opens the same Format window alone for
  a requested volume from File Explorer. Disk Management re-reads UDisks2,
  refuses a missing or protected volume, and still requires the user to
  confirm the data-loss warning before formatting.

Everything goes through UDisks2 with `busctl --system` (`disks.py`
builds the calls, `app.py` runs them in a thread): `Filesystem.Mount` /
`Unmount`, `Drive.Eject`, `Block.Format` (also for a new partition table),
`Partition.Delete`, `Filesystem.SetLabel`,
`PartitionTable.CreatePartitionAndFormat`. UDisks2 asks for the
administrator's password through polkit (the VeltOS prompt) where its
rules require it. The volumes of the running system (`/`, `/boot`,
`/boot/efi`, `/usr`, `/var`, the live medium), EFI/reserved/BIOS boot
partitions, read-only devices and optical discs cannot be formatted or
deleted, and a disk that already has a partition table is never
initialized again. The window re-reads the disks every 5 s while open
(USB sticks) and after every action.

The file systems offered are those whose `mkfs` exists (`ntfs-3g`,
`exfatprogs`, `dosfstools`, `e2fsprogs`: NTFS, exFAT, FAT32, ext4).
Settings > System > Storage and Start's Windows + X menu open it as
"Disk Management"; KDE Partition Manager is no longer in the image.

Tests (`tests/`): `disks.build()` on recorded UDisks2 objects (GPT disk
with EFI + root + unallocated space, an MBR USB stick, an empty DVD
drive), the UDisks2 calls, the backend's permissions and recorded calls
(English and Turkish), and the real window offscreen with every menu and
dialog (any QML warning fails).
