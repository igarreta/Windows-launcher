import uuid

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QMessageBox, QApplication,
)

from ..config_manager import ConfigManager
from ..launcher import EntryLauncher
from ..models import Entry, Folder
from .entry_editor import EntryEditorDialog, NewFolderDialog
from .folder_sidebar import FolderSidebar
from .icon_grid import IconGrid
from .search_bar import SearchBar


class MainWindow(QMainWindow):
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self._cm = config_manager
        self._current_folder_id = ""
        self._setup_window()
        self._setup_ui()
        self._load()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _setup_ui(self):
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        # Root: background overlay
        root = _OverlayWidget(self)
        self.setCentralWidget(root)

        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Left content panel
        content = QWidget()
        content.setObjectName("content")
        content.setStyleSheet("""
            QWidget#content { background-color: rgba(13, 17, 23, 0.97); }
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top bar: search + add button + close button
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #0d1117;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 16, 16, 12)
        top_layout.setSpacing(10)

        self._search = SearchBar()
        self._search.search_changed.connect(self._on_search)
        top_layout.addWidget(self._search, stretch=1)

        add_btn = _icon_btn("+ Add Entry")
        add_btn.clicked.connect(self._add_entry)
        top_layout.addWidget(add_btn)

        close_btn = _icon_btn("✕")
        close_btn.setToolTip("Hide launcher (Escape)")
        close_btn.clicked.connect(self.hide)
        top_layout.addWidget(close_btn)

        content_layout.addWidget(top_bar)

        # Icon grid
        self._grid = IconGrid()
        self._grid.entry_activated.connect(self._launch)
        self._grid.edit_requested.connect(self._edit_entry)
        self._grid.delete_requested.connect(self._delete_entry)
        content_layout.addWidget(self._grid, stretch=1)

        outer.addWidget(content, stretch=1)

        # Right sidebar
        self._sidebar = FolderSidebar()
        self._sidebar.folder_selected.connect(self._on_folder_selected)
        self._sidebar.add_folder_requested.connect(self._add_folder)
        outer.addWidget(self._sidebar)

        # Escape to hide
        esc = QShortcut(QKeySequence("Escape"), self)
        esc.activated.connect(self.hide)

    def _load(self):
        config = self._cm.config
        self._grid.load_config(config)
        self._sidebar.load_folders(config.folders)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            QTimer.singleShot(50, self._search.setFocus)

    def _on_search(self, text: str):
        self._grid.filter_search(text)

    def _on_folder_selected(self, folder_id: str):
        self._current_folder_id = folder_id
        self._grid.filter_folder(folder_id)

    # --- Entry CRUD ---

    def _launch(self, entry: Entry):
        try:
            EntryLauncher.launch(entry)
            self.hide()
        except Exception as e:
            QMessageBox.critical(self, "Launch error", str(e))

    def _add_entry(self):
        config = self._cm.config
        if not config.folders:
            QMessageBox.information(self, "No folders", "Create a folder first using the sidebar.")
            return
        dialog = EntryEditorDialog(
            config=config,
            folder_id=self._current_folder_id or config.folders[0].id,
            parent=self,
        )
        if dialog.exec():
            entry, folder_id, _ = dialog.get_result()
            self._cm.add_entry(folder_id, entry)
            self._grid.add_card(entry, folder_id)
            self._sidebar.load_folders(self._cm.config.folders)

    def _edit_entry(self, entry: Entry, folder_id: str):
        dialog = EntryEditorDialog(
            config=self._cm.config,
            entry=entry,
            folder_id=folder_id,
            parent=self,
        )
        if dialog.exec():
            new_entry, new_folder_id, old_folder_id = dialog.get_result()
            self._cm.update_entry(new_entry, new_folder_id, old_folder_id)
            self._grid.update_card(new_entry, new_folder_id)

    def _delete_entry(self, entry: Entry, folder_id: str):
        reply = QMessageBox.question(
            self, "Delete entry",
            f'Delete "{entry.name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._cm.delete_entry(folder_id, entry.id)
            self._grid.remove_card(entry.id)

    def _add_folder(self):
        dialog = NewFolderDialog(self)
        if dialog.exec():
            name = dialog.folder_name()
            folder = Folder(id=str(uuid.uuid4())[:8], name=name)
            self._cm.add_folder(folder)
            self._sidebar.load_folders(self._cm.config.folders)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Click on the dark overlay background (outside content) hides the window
        child = self.childAt(event.position().toPoint())
        if child is None or child is self.centralWidget():
            self.hide()
        super().mousePressEvent(event)


class _OverlayWidget(QWidget):
    """Semi-transparent background that fills the screen."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160))


def _icon_btn(label: str) -> QPushButton:
    btn = QPushButton(label)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #21262d;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 7px 14px;
            font-size: 13px;
        }
        QPushButton:hover { background-color: #2d333b; }
    """)
    return btn
