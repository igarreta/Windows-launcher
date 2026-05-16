import uuid

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QVBoxLayout, QWidget, QMessageBox, QInputDialog,
)

from ..models import Actionable, Config, Entry, Folder, Logo

_ACTIONABLE_TYPES = ["exe", "bat", "lnk", "ps1", "url", "cmd"]

_FILE_FILTERS = {
    "exe": "Executable (*.exe)",
    "bat": "Batch file (*.bat *.cmd)",
    "lnk": "Shortcut (*.lnk)",
    "ps1": "PowerShell script (*.ps1)",
    "url": "",
    "cmd": "",
}

_DIALOG_STYLE = """
    QDialog {
        background-color: #0d1117;
    }
    QLabel {
        color: #e6edf3;
        font-size: 12px;
    }
    QLineEdit, QComboBox {
        background-color: #21262d;
        color: #e6edf3;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }
    QLineEdit:focus, QComboBox:focus {
        border-color: #58a6ff;
    }
    QComboBox QAbstractItemView {
        background-color: #21262d;
        color: #e6edf3;
        selection-background-color: #1f2937;
    }
    QPushButton {
        background-color: #21262d;
        color: #e6edf3;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 12px;
    }
    QPushButton:hover { background-color: #2d333b; }
    QDialogButtonBox QPushButton[text="OK"] {
        background-color: #1f6feb;
        border-color: #1f6feb;
    }
    QDialogButtonBox QPushButton[text="OK"]:hover {
        background-color: #388bfd;
    }
"""


class EntryEditorDialog(QDialog):
    """Dialog for adding or editing a launcher entry."""

    def __init__(self, config: Config, entry: Entry = None, folder_id: str = None, parent=None):
        super().__init__(parent)
        self._config = config
        self._edit_entry = entry
        self._original_folder_id = folder_id
        self._editing = entry is not None

        self.setWindowTitle("Edit Entry" if self._editing else "Add Entry")
        self.setMinimumWidth(480)
        self.setStyleSheet(_DIALOG_STYLE)
        self._build_ui()
        if self._editing:
            self._populate(entry, folder_id)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Name
        self._name = QLineEdit()
        self._name.setPlaceholderText("Display name")
        form.addRow("Name *", self._name)

        # Description
        self._desc = QLineEdit()
        self._desc.setPlaceholderText("Short description")
        form.addRow("Description", self._desc)

        # Folder
        self._folder_combo = QComboBox()
        for folder in self._config.folders:
            self._folder_combo.addItem(folder.name, folder.id)
        form.addRow("Folder *", self._folder_combo)

        # Actionable type
        self._type_combo = QComboBox()
        self._type_combo.addItems(_ACTIONABLE_TYPES)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        form.addRow("Type *", self._type_combo)

        # Path + browse
        path_row = QWidget()
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(6)
        self._path = QLineEdit()
        self._path.setPlaceholderText("Path or URL")
        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(self._path)
        path_layout.addWidget(self._browse_btn)
        form.addRow("Path *", path_row)

        # Args
        self._args = QLineEdit()
        self._args.setPlaceholderText("Optional arguments, space-separated")
        form.addRow("Arguments", self._args)

        # Working directory
        self._workdir = QLineEdit()
        self._workdir.setPlaceholderText("Leave empty to use default")
        form.addRow("Working dir", self._workdir)

        # Logo source
        self._logo_source = QComboBox()
        self._logo_source.addItems(["auto", "file", "url"])
        self._logo_source.currentTextChanged.connect(self._on_logo_source_changed)
        form.addRow("Logo source", self._logo_source)

        # Logo value
        logo_row = QWidget()
        logo_layout = QHBoxLayout(logo_row)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(6)
        self._logo_value = QLineEdit()
        self._logo_value.setPlaceholderText("Path or URL (when source is file/url)")
        self._logo_browse_btn = QPushButton("Browse…")
        self._logo_browse_btn.clicked.connect(self._browse_logo)
        logo_layout.addWidget(self._logo_value)
        logo_layout.addWidget(self._logo_browse_btn)
        form.addRow("Logo value", logo_row)

        layout.addLayout(form)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_type_changed(self._type_combo.currentText())
        self._on_logo_source_changed(self._logo_source.currentText())

    def _populate(self, entry: Entry, folder_id: str):
        self._name.setText(entry.name)
        self._desc.setText(entry.description)

        idx = self._folder_combo.findData(folder_id)
        if idx >= 0:
            self._folder_combo.setCurrentIndex(idx)

        type_idx = self._type_combo.findText(entry.actionable.type)
        if type_idx >= 0:
            self._type_combo.setCurrentIndex(type_idx)

        self._path.setText(entry.actionable.path)
        self._args.setText(" ".join(entry.actionable.args))
        self._workdir.setText(entry.actionable.working_dir or "")

        src_idx = self._logo_source.findText(entry.logo.source)
        if src_idx >= 0:
            self._logo_source.setCurrentIndex(src_idx)
        self._logo_value.setText(entry.logo.value or "")

    def _on_type_changed(self, type_str: str):
        is_path_type = type_str not in ("url", "cmd")
        self._browse_btn.setEnabled(is_path_type)

    def _on_logo_source_changed(self, source: str):
        is_custom = source in ("file", "url")
        self._logo_value.setEnabled(is_custom)
        self._logo_browse_btn.setEnabled(source == "file")

    def _browse(self):
        type_str = self._type_combo.currentText()
        file_filter = _FILE_FILTERS.get(type_str, "All files (*)")
        path, _ = QFileDialog.getOpenFileName(self, "Select file", "", file_filter)
        if path:
            self._path.setText(path.replace("/", "\\"))

    def _browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select logo image", "", "Images (*.png *.jpg *.jpeg *.ico *.bmp *.svg)"
        )
        if path:
            self._logo_value.setText(path.replace("/", "\\"))

    def _accept(self):
        name = self._name.text().strip()
        path = self._path.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation", "Name is required.")
            return
        if not path:
            QMessageBox.warning(self, "Validation", "Path is required.")
            return
        if self._folder_combo.count() == 0:
            QMessageBox.warning(self, "Validation", "Create a folder first.")
            return

        self.accept()

    def get_result(self) -> tuple:
        """Returns (entry, folder_id, original_folder_id)."""
        args = [a for a in self._args.text().split() if a]
        entry = Entry(
            id=self._edit_entry.id if self._editing else str(uuid.uuid4())[:8],
            name=self._name.text().strip(),
            description=self._desc.text().strip(),
            actionable=Actionable(
                type=self._type_combo.currentText(),
                path=self._path.text().strip(),
                args=args,
                working_dir=self._workdir.text().strip() or None,
            ),
            logo=Logo(
                source=self._logo_source.currentText(),
                value=self._logo_value.text().strip() or None,
            ),
        )
        folder_id = self._folder_combo.currentData()
        return entry, folder_id, self._original_folder_id


class NewFolderDialog(QDialog):
    """Simple dialog to create a new folder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Folder")
        self.setStyleSheet(_DIALOG_STYLE)
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Folder name:"))
        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. Dev Tools")
        layout.addWidget(self._name)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept(self):
        if not self._name.text().strip():
            return
        self.accept()

    def folder_name(self) -> str:
        return self._name.text().strip()
