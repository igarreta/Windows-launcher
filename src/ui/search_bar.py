from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QLineEdit


class SearchBar(QLineEdit):
    search_changed = Signal(str)

    _STYLE = """
        QLineEdit {
            background-color: #21262d;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border-color: #58a6ff;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Search...")
        self.setStyleSheet(self._STYLE)
        self.setClearButtonEnabled(True)
        self.textChanged.connect(self.search_changed)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.clear()
        super().keyPressEvent(event)
