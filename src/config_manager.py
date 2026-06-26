import json
import uuid
from pathlib import Path

from .models import Config, Entry, Folder, Settings


class ConfigManager:
    def __init__(self, path: str):
        self._path = Path(path)
        self._config: Config = self._load()

    def _load(self) -> Config:
        if not self._path.exists():
            config = Config(folders=[], settings=Settings())
            self._save(config)
            return config
        try:
            with open(self._path, encoding="utf-8") as f:
                return Config.from_dict(json.load(f))
        except Exception:
            return Config(folders=[], settings=Settings())

    def _save(self, config: Config) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

    @property
    def config(self) -> Config:
        return self._config

    def save(self) -> None:
        self._save(self._config)

    def reload(self) -> None:
        self._config = self._load()

    # --- Entry operations ---

    def add_entry(self, folder_id: str, entry: Entry) -> None:
        folder = self._config.find_folder(folder_id)
        if folder is None:
            raise ValueError(f"Folder '{folder_id}' not found")
        if not entry.id:
            entry.id = str(uuid.uuid4())[:8]
        folder.entries.append(entry)
        self.save()

    def update_entry(self, entry: Entry, new_folder_id: str, old_folder_id: str) -> None:
        old_folder = self._config.find_folder(old_folder_id)
        if old_folder:
            old_folder.entries = [e for e in old_folder.entries if e.id != entry.id]

        new_folder = self._config.find_folder(new_folder_id)
        if new_folder is None:
            raise ValueError(f"Folder '{new_folder_id}' not found")
        new_folder.entries.append(entry)
        self.save()

    def delete_entry(self, folder_id: str, entry_id: str) -> None:
        folder = self._config.find_folder(folder_id)
        if folder:
            folder.entries = [e for e in folder.entries if e.id != entry_id]
            self.save()

    def move_entry(self, folder_id: str, entry_id: str, offset: int) -> bool:
        """Move an entry within its folder by `offset` positions (-1 left,
        +1 right). Returns True if the order changed (and was saved)."""
        folder = self._config.find_folder(folder_id)
        if folder is None:
            return False
        entries = folder.entries
        idx = next((i for i, e in enumerate(entries) if e.id == entry_id), None)
        if idx is None:
            return False
        new_idx = idx + offset
        if new_idx < 0 or new_idx >= len(entries):
            return False
        entries.insert(new_idx, entries.pop(idx))
        self.save()
        return True

    # --- Folder operations ---

    def add_folder(self, folder: Folder) -> None:
        if not folder.id:
            folder.id = str(uuid.uuid4())[:8]
        self._config.folders.append(folder)
        self.save()

    def update_folder_name(self, folder_id: str, name: str) -> None:
        folder = self._config.find_folder(folder_id)
        if folder:
            folder.name = name
            self.save()

    def delete_folder(self, folder_id: str) -> None:
        self._config.folders = [f for f in self._config.folders if f.id != folder_id]
        self.save()
