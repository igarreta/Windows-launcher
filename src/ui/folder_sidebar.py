from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy
)

from ..models import Folder


_ALL_ID = ""

_SIDEBAR_STYLE = """
    QWidget#sidebar {
        background-color: #161b22;
        border-right: 1px solid #21262d;
    }
"""

_BTN_BASE = """
    QPushButton {
        text-align: left;
        padding: 10px 16px;
        border: none;
        border-radius: 6px;
        color: #8b949e;
        font-size: 13px;
        background: transparent;
    }
    QPushButton:hover {
        background-color: #21262d;
        color: #e6edf3;
    }
"""

_BTN_ACTIVE = """
    QPushButton {
        text-align: left;
        padding: 10px 16px;
        border: none;
        border-radius: 6px;
        color: #58a6ff;
        font-size: 13px;
        font-weight: 600;
        background-color: #1f2937;
    }
"""


class FolderSidebar(QWidget):
    folder_selected = Signal(str)   # folder_id, "" = All
    add_folder_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        # QWidget subclasses don't paint a stylesheet background unless this
        # attribute is set — without it the sidebar looks transparent.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(210)
        self.setStyleSheet(_SIDEBAR_STYLE)

        self._buttons: dict[str, QPushButton] = {}
        self._active_id = _ALL_ID
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QLabel("Folders")
        header.setStyleSheet(
            "color: #8b949e; font-size: 11px; font-weight: 600;"
            "padding: 16px 16px 8px 16px; letter-spacing: 1px;"
        )
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._btn_container = QWidget()
        self._btn_container.setStyleSheet("background: transparent;")
        self._btn_layout = QVBoxLayout(self._btn_container)
        self._btn_layout.setContentsMargins(8, 0, 8, 8)
        self._btn_layout.setSpacing(2)
        self._btn_layout.addStretch()

        scroll.setWidget(self._btn_container)
        outer.addWidget(scroll, stretch=1)

        add_btn = QPushButton("+ New Folder")
        add_btn.setStyleSheet(_BTN_BASE)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.add_folder_requested)
        outer.addWidget(add_btn)

        self._add_folder_btn(Folder(id=_ALL_ID, name="All"))

    def load_folders(self, folders: list) -> None:
        for btn_id in list(self._buttons.keys()):
            if btn_id != _ALL_ID:
                btn = self._buttons.pop(btn_id)
                self._btn_layout.removeWidget(btn)
                btn.deleteLater()

        for folder in folders:
            self._add_folder_btn(folder)

        self._highlight(self._active_id)

    def _add_folder_btn(self, folder: Folder) -> None:
        btn = QPushButton(folder.name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(_BTN_BASE)
        btn.clicked.connect(lambda checked, fid=folder.id: self._on_click(fid))

        insert_pos = self._btn_layout.count() - 1  # before stretch
        self._btn_layout.insertWidget(insert_pos, btn)
        self._buttons[folder.id] = btn

    def _on_click(self, folder_id: str) -> None:
        self._active_id = folder_id
        self._highlight(folder_id)
        self.folder_selected.emit(folder_id)

    def _highlight(self, active_id: str) -> None:
        for fid, btn in self._buttons.items():
            btn.setStyleSheet(_BTN_ACTIVE if fid == active_id else _BTN_BASE)
