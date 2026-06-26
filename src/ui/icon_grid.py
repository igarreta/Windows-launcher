from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QScrollArea, QWidget

from ..models import Config, Entry
from ..icon_resolver import IconResolver
from .entry_card import EntryCard
from .flow_layout import FlowLayout


class IconGrid(QScrollArea):
    entry_activated = Signal(object)            # Entry
    edit_requested = Signal(object, str)        # Entry, folder_id
    duplicate_requested = Signal(object, str)   # Entry, folder_id
    delete_requested = Signal(object, str)      # Entry, folder_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: list[EntryCard] = []
        self._current_folder = ""   # "" = All
        self._search_text = ""
        self._setup_ui()

    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #0d1117; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #30363d; border-radius: 4px; min-height: 20px;
            }
        """)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._flow = FlowLayout(self._container, h_spacing=12, v_spacing=12)
        self._flow.setContentsMargins(20, 20, 20, 20)
        self._container.setLayout(self._flow)
        self.setWidget(self._container)

    def load_config(self, config: Config) -> None:
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        for folder in config.folders:
            for entry in folder.entries:
                card = EntryCard(entry, folder.id, parent=self._container)
                card.activated.connect(self.entry_activated)
                card.edit_requested.connect(self.edit_requested)
                card.duplicate_requested.connect(self.duplicate_requested)
                card.delete_requested.connect(self.delete_requested)
                self._flow.addWidget(card)
                self._cards.append(card)
                self._load_icon_async(card, entry)

        self._apply_filters()

    def add_card(self, entry: Entry, folder_id: str) -> None:
        card = EntryCard(entry, folder_id, parent=self._container)
        card.activated.connect(self.entry_activated)
        card.edit_requested.connect(self.edit_requested)
        card.duplicate_requested.connect(self.duplicate_requested)
        card.delete_requested.connect(self.delete_requested)
        self._flow.addWidget(card)
        self._cards.append(card)
        self._load_icon_async(card, entry)
        self._apply_filters()

    def remove_card(self, entry_id: str) -> None:
        for card in self._cards:
            if card.entry.id == entry_id:
                self._cards.remove(card)
                card.setParent(None)
                card.deleteLater()
                break
        self._apply_filters()

    def update_card(self, entry: Entry, folder_id: str) -> None:
        for card in self._cards:
            if card.entry.id == entry.id:
                card.update_entry(entry, folder_id)
                self._load_icon_async(card, entry)
                break
        self._apply_filters()

    def filter_folder(self, folder_id: str) -> None:
        self._current_folder = folder_id
        self._apply_filters()

    def filter_search(self, text: str) -> None:
        self._search_text = text.lower()
        self._apply_filters()

    def _apply_filters(self):
        for card in self._cards:
            visible = self._is_visible(card)
            card.setVisible(visible)
        self._container.adjustSize()
        self._container.update()

    def _is_visible(self, card: EntryCard) -> bool:
        if self._current_folder and card.folder_id != self._current_folder:
            return False
        if self._search_text:
            haystack = (card.entry.name + " " + card.entry.description).lower()
            if self._search_text not in haystack:
                return False
        return True

    def _load_icon_async(self, card: EntryCard, entry: Entry) -> None:
        try:
            px = IconResolver.resolve(entry)
            card.set_icon(px)
        except Exception:
            pass
