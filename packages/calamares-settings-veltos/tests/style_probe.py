#!/usr/bin/python3
"""Runs the installer's Qt style plugin against stand-ins for Calamares'
partition views and prints what it drew, as JSON (used by test_style.py).

    style_probe.py THEME-ARGUMENT [LOCALE]

TEST DOUBLES: PartitionBarsView, PartitionLabelsView, PartitionSplitterWidget
and DeviceModel below are small PySide6 classes with the class names of
Calamares' own (the plugin recognises them by name); they lay out their
parts as simply as possible and paint nothing themselves. Calamares' real
classes were checked in the dev VM (docs/dev/development-log.md).
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QLocale, QModelIndex, QPoint, QRect, QSize, Qt, Signal  # noqa: E402
from PySide6.QtGui import QColor, QIcon, QPixmap, QRegion, QStandardItem, QStandardItemModel  # noqa: E402
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFrame, QLabel,  # noqa: E402
                               QSizePolicy, QStyledItemDelegate, QStyleFactory, QVBoxLayout, QWidget)

SIZE, FREE, NEW, FS_LABEL, FS_TYPE, PATH = range(Qt.ItemDataRole.UserRole + 1, Qt.ItemDataRole.UserRole + 7)
GIB = 1024 ** 3
MIB = 1024 ** 2
QSS = Path(__file__).resolve().parent.parent / "calamares/branding/veltos/stylesheet-light.qss"


def partition_model(rows):
    """rows: (path, size, fs name, fs type, free, new, mount, label)."""
    model = QStandardItemModel(0, 5)
    for path, size, fs, fs_type, free, new, mount, label in rows:
        name = QStandardItem(path)
        for role, value in ((SIZE, size), (FREE, free), (NEW, new), (FS_LABEL, label),
                            (FS_TYPE, fs_type), (PATH, path)):
            name.setData(value, role)
        model.appendRow([name, QStandardItem(fs), QStandardItem(label), QStandardItem(mount),
                         QStandardItem(f"{size / GIB:.2f} GiB")])
    return model


class PartitionBarsView(QAbstractItemView):
    """TEST DOUBLE of Calamares' bars: parts side by side by size."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # As Calamares' views: no frame, as tall as their size hint.
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def rects(self):
        model = self.model()
        rows = [model.index(row, 0) for row in range(model.rowCount())]
        total = sum(index.data(SIZE) for index in rows) or 1
        x, out = 0, []
        for n, index in enumerate(rows):
            width = self.width() - x if n == len(rows) - 1 else int(self.width() * index.data(SIZE) / total)
            out.append((index, QRect(x, 0, width, self.height())))
            x += width
        return out

    def visualRect(self, index):
        for candidate, rect in self.rects():
            if candidate == index:
                return rect
        return QRect()

    def indexAt(self, point):
        for index, rect in self.rects():
            if rect.contains(point):
                return index
        return QModelIndex()

    def sizeHint(self):
        return QSize(-1, 30)

    def minimumSizeHint(self):
        return self.sizeHint()

    def horizontalOffset(self):
        return 0

    def verticalOffset(self):
        return 0

    def isIndexHidden(self, index):
        return False

    def moveCursor(self, action, modifiers):
        return QModelIndex()

    def scrollTo(self, index, hint=QAbstractItemView.ScrollHint.EnsureVisible):
        pass

    def setSelection(self, rect, flags):
        pass

    def visualRegionForSelection(self, selection):
        return QRegion()


class PartitionLabelsView(PartitionBarsView):
    """TEST DOUBLE of Calamares' legend: 160 px per partition."""

    def rects(self):
        model = self.model()
        return [(model.index(row, 0), QRect(row * 160, 0, 150, 36)) for row in range(model.rowCount())]

    def sizeHint(self):
        return QSize(-1, 44)


class PartitionSplitterWidget(QWidget):
    """TEST DOUBLE of Calamares' resize bar (only its signal)."""
    partitionResized = Signal(str, "qint64", "qint64")

    def sizeHint(self):
        return QSize(-1, 30)


class DeviceModel(QStandardItemModel):
    """TEST DOUBLE of Calamares' disk list."""


def colour(image, x, y):
    return QColor(image.pixel(x, y)).name().upper()


def main():
    app = QApplication(["style_probe", sys.argv[1]])
    if len(sys.argv) > 2:
        QLocale.setDefault(QLocale(sys.argv[2]))
    result = {"keys": [key.lower() for key in QStyleFactory.keys()]}
    style = QStyleFactory.create("veltos-installer")
    result["created"] = style is not None
    app.setStyle(style)
    app.setStyleSheet(QSS.read_text(encoding="utf-8"))

    disk = [("/dev/vda1", 4 * GIB, "FAT32", 7, False, False, "", ""),
            ("/dev/vda2", 16 * MIB, "unknown", 0, False, False, "", ""),
            ("/dev/vda3", 20 * GIB, "NTFS", 8, False, False, "", "Windows"),
            ("Free Space", 16 * GIB, "", 0, True, False, "", "")]
    after = [("", 4 * GIB, "FAT32", 7, False, True, "/boot/efi", ""),
             ("", 8 * GIB, "ext4", 4, False, True, "/boot", "boot"),
             ("", 28 * GIB, "ext4", 4, False, True, "/", "veltos")]

    window = QWidget()
    layout = QVBoxLayout(window)
    before_frame = QWidget(objectName="m_previewBeforeFrame")
    QVBoxLayout(before_frame)
    bars = PartitionBarsView(before_frame)
    bars.setModel(partition_model(disk))
    before_frame.layout().addWidget(bars)
    legend = PartitionLabelsView()
    legend.setModel(bars.model())
    new_bars = PartitionBarsView()
    new_bars.setModel(partition_model(after))
    splitter = PartitionSplitterWidget()
    label = QLabel("/dev/vda3 will be shrunk to 1628MiB and a new 22630MiB partition will be created for VeltOS.")
    # Calamares' Turkish translation writes "MB" for its MiB values.
    translated = QLabel("/dev/vda3, 1628 MB olarak küçültülecek ve VeltOS için yeni bir 22630 MB  bölüm; 300 MB EFI")
    disks = DeviceModel()
    disk_icon = QPixmap(64, 64)
    disk_icon.fill(QColor("#5D6475"))
    for text in ("vda - 40.00 GiB (/dev/vda)", "sdb - 931.51 GiB (/dev/sdb)"):
        disks.appendRow(QStandardItem(QIcon(disk_icon), text))
    combo = QComboBox()
    combo.setModel(disks)
    combo.setCurrentIndex(1)
    changes = []
    combo.currentIndexChanged.connect(changes.append)
    for widget in (before_frame, legend, new_bars, splitter, label, translated, combo):
        layout.addWidget(widget)
    window.resize(800, 400)
    window.show()
    app.processEvents()
    splitter.partitionResized.emit("/dev/vda3", 8 * GIB, 12 * GIB)
    app.processEvents()

    image = bars.grab().toImage()
    rects = dict((index.row(), rect) for index, rect in bars.rects())
    result["bars"] = {name: colour(image, rects[row].center().x(), rects[row].center().y())
                      for row, name in ((0, "efi"), (2, "windows"))}
    result["bars"]["background"] = colour(image, 2, image.height() - 1)
    free = rects[3]
    result["bars"]["free"] = sorted({colour(image, x, free.center().y()) for x in range(free.left() + 4, free.right() - 4)})
    image = new_bars.grab().toImage()
    rects = dict((index.row(), rect) for index, rect in new_bars.rects())
    result["new"] = {name: colour(image, rects[row].center().x(), rects[row].center().y())
                     for row, name in ((0, "efi"), (1, "boot"), (2, "root"))}

    image = legend.grab().toImage()
    pixels = [colour(image, x, y) for x in range(image.width()) for y in range(image.height())]
    result["legend"] = {"background": colour(image, image.width() - 2, image.height() - 2),
                        "black": pixels.count("#000000"),
                        "squares": [colour(image, row * 160 + 7, 4 + legend.fontMetrics().height() // 2)
                                    for row in range(4)],
                        "inked": sum(1 for p in set(pixels))}

    image = splitter.grab().toImage()
    # Calamares' arithmetic: parts below 1 % of the disk count as 1 %.
    sizes = [4 * GIB, 16 * MIB, 8 * GIB, 12 * GIB, 16 * GIB]
    total = adjusted = sum(sizes)
    for n, size in enumerate(sizes):
        if size < 0.01 * total:
            adjusted += int(0.01 * total) - size
            sizes[n] = int(0.01 * total)
    handle = 0
    for size in sizes[:3]:
        handle = int(handle + splitter.width() * (size / adjusted))
    result["splitter"] = {"width": splitter.width(), "handle": handle,
                          "new": colour(image, handle + 40, splitter.height() // 2),
                          "shrunk": colour(image, handle - 40, splitter.height() // 2),
                          "thumb": colour(image, handle - 3, 4)}

    combo.showPopup()
    app.processEvents()
    popup = combo.view().window()
    result["popup"] = {"top": popup.geometry().top(),
                       "box_bottom": combo.mapToGlobal(combo.rect().bottomLeft()).y(),
                       "left": popup.geometry().left(),
                       "box_left": combo.mapToGlobal(combo.rect().topLeft()).x()}
    combo.hidePopup()

    result["label"] = label.text()
    result["translated"] = translated.text()
    result["combo"] = {"text": combo.currentText(), "index": combo.currentIndex(), "changes": changes,
                       "rows": combo.count(), "items": [combo.itemText(n) for n in range(combo.count())],
                       "delegate": isinstance(combo.itemDelegate(), QStyledItemDelegate),
                       "row_height": combo.view().sizeHintForRow(0),
                       "model": type(combo.model()).__name__}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
