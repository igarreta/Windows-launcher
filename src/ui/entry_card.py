import subprocess
import os

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QFontMetrics
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QMenu, QSizePolicy
)

from ..models import Entry


class EntryCard(QFrame):
    activated = Signal(object)      # Entry
    edit_requested = Signal(object, str)    # Entry, folder_id
    delete_requested = Signal(object, str)  # Entry, folder_id

    CARD_W = 120
    CARD_H = 150
    ICON_SIZE = 56

    _STYLE = """
        EntryCard {
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 10px;
        }
        EntryCard:hover {
            background-color: #2d333b;
            border-color: #58a6ff;
        }
    """

    def __init__(self, entry: Entry, folder_id: str, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._folder_id = folder_id
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._STYLE)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(4)

        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setFixedSize(self.ICON_SIZE, self.ICON_SIZE)
        layout.addWidget(self._icon_lbl)

        self._name_lbl = QLabel(_elide(self._entry.name, self.CARD_W - 16, lines=2))
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_lbl.setWordWrap(True)
        self._name_lbl.setStyleSheet("color: #e6edf3; font-size: 11px; font-weight: 600;")
        self._name_lbl.setMaximumHeight(36)
        layout.addWidget(self._name_lbl)

        if self._entry.description:
            self._desc_lbl = QLabel(_elide(self._entry.description, self.CARD_W - 16))
            self._desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._desc_lbl.setStyleSheet("color: #8b949e; font-size: 9px;")
            layout.addWidget(self._desc_lbl)

    def set_icon(self, pixmap: QPixmap):
        self._icon_lbl.setPixmap(
            pixmap.scaled(
                self.ICON_SIZE, self.ICON_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    @property
    def entry(self) -> Entry:
        return self._entry

    @property
    def folder_id(self) -> str:
        return self._folder_id

    def update_entry(self, entry: Entry, folder_id: str):
        self._entry = entry
        self._folder_id = folder_id
        self._name_lbl.setText(_elide(entry.name, self.CARD_W - 16, lines=2))
        if hasattr(self, "_desc_lbl"):
            self._desc_lbl.setText(_elide(entry.description, self.CARD_W - 16))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self._entry)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_STYLE)
        edit_act = menu.addAction("Edit")
        delete_act = menu.addAction("Delete")
        open_loc_act = None
        if self._entry.actionable.type not in ("url", "cmd"):
            menu.addSeparator()
            open_loc_act = menu.addAction("Open file location")

        chosen = menu.exec(event.globalPos())
        if chosen == edit_act:
            self.edit_requested.emit(self._entry, self._folder_id)
        elif chosen == delete_act:
            self.delete_requested.emit(self._entry, self._folder_id)
        elif open_loc_act and chosen == open_loc_act:
            path = self._entry.actionable.path
            if os.path.exists(path):
                subprocess.Popen(["explorer", f"/select,{path}"])


_MENU_STYLE = """
    QMenu {
        background-color: #161b22;
        color: #e6edf3;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 4px;
    }
    QMenu::item { padding: 6px 20px; border-radius: 4px; }
    QMenu::item:selected { background-color: #21262d; }
    QMenu::separator { height: 1px; background: #30363d; margin: 4px 0; }
"""


def _elide(text: str, width: int, lines: int = 1) -> str:
    from PySide6.QtGui import QFont, QFontMetrics
    fm = QFontMetrics(QFont())
    if lines > 1:
        return text
    return fm.elidedText(text, Qt.TextElideMode.ElideRight, width)
