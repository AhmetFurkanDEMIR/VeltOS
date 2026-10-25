# Safely Remove Hardware in Windows 11's design (2026-10-25, dev VM)

Item 30 of the product owner's 2026-10-23 list. QEMU dev VM (Turkish
session); a removable test drive made with `modprobe scsi_debug removable=1
dev_size_mb=64`, a DOS partition table and a FAT volume labelled
"USB BELLEK"; the live DVD is the second entry.

| Picture | What it shows |
|---|---|
| `before-plasma-flyout.png` | Before: Plasma's flyout with a heading (back arrow, title, "..."), drive icons, usage bars and buttons |
| `before-after-eject.png` | Before: after an eject Plasma only wrote "Bu aygıt artık güvenli olarak kaldırılabilir." in the row |
| `menu.png` | Now: a small menu without heading, as tall as its entries: "USB BELLEK aygıtını çıkar" / "VeltOS 0.1.0-dev amd64 aygıtını çıkar" with the size under each |
| `ejected-notification.png` | The USB entry clicked: the menu closed, the volume was unmounted (`findmnt` printed nothing), and Windows' notification came: "Donanımı güvenle kaldırabilirsiniz — 'USB BELLEK' aygıtı artık bilgisayardan güvenle çıkarılabilir." |
| `in-use-notification.png` | A shell kept the volume busy (`cd` into it): "USB BELLEK çıkarılırken sorun oluştu — Aygıtı kullanıyor olabilecek programları veya pencereleri kapatın ve yeniden deneyin."; the volume stayed mounted |
| `hover-and-plasma-message.png` | The entry under the pointer is highlighted; after the failed eject Plasma's own reason shows under it |

Not tested with a real USB stick or card reader.
