from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Actionable:
    type: str  # "exe" | "bat" | "lnk" | "url" | "ps1" | "cmd"
    path: str
    args: list = field(default_factory=list)
    working_dir: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "path": self.path,
            "args": self.args,
            "working_dir": self.working_dir,
        }

    @staticmethod
    def from_dict(d: dict) -> "Actionable":
        return Actionable(
            type=d["type"],
            path=d["path"],
            args=d.get("args", []),
            working_dir=d.get("working_dir"),
        )


@dataclass
class Logo:
    source: str = "auto"  # "auto" | "file" | "url"
    value: Optional[str] = None

    def to_dict(self) -> dict:
        return {"source": self.source, "value": self.value}

    @staticmethod
    def from_dict(d: dict) -> "Logo":
        return Logo(source=d.get("source", "auto"), value=d.get("value"))


@dataclass
class Entry:
    id: str
    name: str
    description: str
    actionable: Actionable
    logo: Logo

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "actionable": self.actionable.to_dict(),
            "logo": self.logo.to_dict(),
        }

    @staticmethod
    def from_dict(d: dict) -> "Entry":
        return Entry(
            id=d["id"],
            name=d["name"],
            description=d.get("description", ""),
            actionable=Actionable.from_dict(d["actionable"]),
            logo=Logo.from_dict(d.get("logo", {})),
        )


@dataclass
class Folder:
    id: str
    name: str
    entries: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "entries": [e.to_dict() for e in self.entries],
        }

    @staticmethod
    def from_dict(d: dict) -> "Folder":
        return Folder(
            id=d["id"],
            name=d["name"],
            entries=[Entry.from_dict(e) for e in d.get("entries", [])],
        )


@dataclass
class Settings:
    global_hotkey: str = "Alt+Space"
    columns: int = 6

    def to_dict(self) -> dict:
        return {"global_hotkey": self.global_hotkey, "columns": self.columns}

    @staticmethod
    def from_dict(d: dict) -> "Settings":
        return Settings(
            global_hotkey=d.get("global_hotkey", "Alt+Space"),
            columns=d.get("columns", 6),
        )


@dataclass
class Config:
    folders: list = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)

    def to_dict(self) -> dict:
        return {
            "folders": [f.to_dict() for f in self.folders],
            "settings": self.settings.to_dict(),
        }

    @staticmethod
    def from_dict(d: dict) -> "Config":
        return Config(
            folders=[Folder.from_dict(f) for f in d.get("folders", [])],
            settings=Settings.from_dict(d.get("settings", {})),
        )

    def find_entry(self, entry_id: str) -> Optional[tuple]:
        """Returns (folder, entry) or None."""
        for folder in self.folders:
            for entry in folder.entries:
                if entry.id == entry_id:
                    return folder, entry
        return None

    def find_folder(self, folder_id: str) -> Optional["Folder"]:
        for folder in self.folders:
            if folder.id == folder_id:
                return folder
        return None
