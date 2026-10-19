"""The Processes list as a Qt model that is updated in place every second:
rows that stay keep their delegates (scroll position, hover, selection);
only processes that start or end are inserted or removed."""

from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt

ROLES = ("kind", "key", "name", "icon", "count", "cpuText", "cpu", "memoryText", "memoryShare", "title")


class RowsModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []

    def roleNames(self):
        return {Qt.UserRole + i: QByteArray(name.encode()) for i, name in enumerate(ROLES)}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        offset = role - Qt.UserRole
        if 0 <= offset < len(ROLES):
            return self._rows[index.row()].get(ROLES[offset])
        return None

    def rows(self):
        return list(self._rows)

    def sync(self, target):
        """Make the rows equal to `target` (dicts with a unique "key")."""
        i = 0
        while i < len(target):
            want = target[i]
            if i < len(self._rows) and self._rows[i]["key"] == want["key"]:
                if self._rows[i] != want:
                    self._rows[i] = want
                    self.dataChanged.emit(self.index(i), self.index(i))
                i += 1
                continue
            later = next((j for j in range(i + 1, len(self._rows)) if self._rows[j]["key"] == want["key"]), None)
            if later is not None:
                # Rows before the wanted one are gone (or moved): remove them.
                self.beginRemoveRows(QModelIndex(), i, later - 1)
                del self._rows[i:later]
                self.endRemoveRows()
                continue
            self.beginInsertRows(QModelIndex(), i, i)
            self._rows.insert(i, want)
            self.endInsertRows()
            i += 1
        if len(self._rows) > len(target):
            self.beginRemoveRows(QModelIndex(), len(target), len(self._rows) - 1)
            del self._rows[len(target):]
            self.endRemoveRows()
