import os
import io
import hashlib
from pathlib import Path
from typing import Optional

from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize

from .models import Entry

_CACHE_DIR = Path("icon_cache")

try:
    import icoextract
    _HAS_ICOEXTRACT = True
except ImportError:
    _HAS_ICOEXTRACT = False

try:
    import win32com.client
    _HAS_WIN32COM = True
except ImportError:
    _HAS_WIN32COM = False

try:
    from PIL import Image
    _HAS_PILLOW = True
except ImportError:
    _HAS_PILLOW = False


class IconResolver:
    @staticmethod
    def resolve(entry: Entry, size: int = 64) -> QPixmap:
        logo = entry.logo
        actionable = entry.actionable

        if logo.source == "file" and logo.value:
            px = IconResolver._from_file(logo.value, size)
            if px:
                return px

        if logo.source == "url" and logo.value:
            px = IconResolver._from_url(logo.value, size)
            if px:
                return px

        if logo.source == "auto":
            if actionable.type in ("exe", "bat", "ps1", "cmd"):
                px = IconResolver._from_exe(actionable.path, size)
                if px:
                    return px
            elif actionable.type == "lnk":
                px = IconResolver._from_lnk(actionable.path, size)
                if px:
                    return px

        return IconResolver._fallback(actionable.type, size)

    @staticmethod
    def _from_exe(path: str, size: int) -> Optional[QPixmap]:
        if not _HAS_ICOEXTRACT or not os.path.isfile(path):
            return None
        try:
            cache_key = _cache_key(path)
            cached = _load_cache(cache_key)
            if cached:
                return cached

            extractor = icoextract.IconExtractor(path)
            icon_data = extractor.get_icon()
            if icon_data is None:
                return None

            px = _pil_bytes_to_pixmap(icon_data.getvalue(), size)
            if px:
                _save_cache(cache_key, px)
            return px
        except Exception:
            return None

    @staticmethod
    def _from_lnk(path: str, size: int) -> Optional[QPixmap]:
        if not _HAS_WIN32COM or not os.path.isfile(path):
            return None
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            link = shell.CreateShortCut(path)
            target = link.TargetPath
            if target and os.path.isfile(target):
                return IconResolver._from_exe(target, size)
        except Exception:
            pass
        return None

    @staticmethod
    def _from_file(path: str, size: int) -> Optional[QPixmap]:
        if not os.path.isfile(path):
            return None
        px = QPixmap(path)
        if px.isNull():
            return None
        return px.scaled(size, size, aspectMode=_KEEP_RATIO, mode=_SMOOTH)

    @staticmethod
    def _from_url(url: str, size: int) -> Optional[QPixmap]:
        cache_key = _cache_key(url)
        cached = _load_cache(cache_key)
        if cached:
            return cached
        try:
            import requests
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            px = _pil_bytes_to_pixmap(resp.content, size)
            if px:
                _save_cache(cache_key, px)
            return px
        except Exception:
            return None

    @staticmethod
    def _fallback(actionable_type: str, size: int) -> QPixmap:
        style = QApplication.style()
        sp_map = {
            "exe": 6,   # SP_ComputerIcon
            "bat": 24,  # SP_DriveHDIcon
            "cmd": 24,
            "ps1": 24,
            "lnk": 23,  # SP_FileLinkIcon
            "url": 14,  # SP_DriveNetIcon
        }
        sp = sp_map.get(actionable_type, 0)  # 0 = SP_TitleBarMenuButton fallback
        icon: QIcon = style.standardIcon(sp)
        px = icon.pixmap(QSize(size, size))
        if px.isNull():
            px = QPixmap(size, size)
            px.fill()
        return px


# --- Helpers ---

from PySide6.QtCore import Qt as _Qt
_KEEP_RATIO = _Qt.AspectRatioMode.KeepAspectRatio
_SMOOTH = _Qt.TransformationMode.SmoothTransformation


def _cache_key(source: str) -> str:
    return hashlib.md5(source.encode()).hexdigest()


def _load_cache(key: str) -> Optional[QPixmap]:
    path = _CACHE_DIR / f"{key}.png"
    if path.exists():
        px = QPixmap(str(path))
        if not px.isNull():
            return px
    return None


def _save_cache(key: str, px: QPixmap) -> None:
    try:
        _CACHE_DIR.mkdir(exist_ok=True)
        px.save(str(_CACHE_DIR / f"{key}.png"))
    except Exception:
        pass


def _pil_bytes_to_pixmap(data: bytes, size: int) -> Optional[QPixmap]:
    if not _HAS_PILLOW:
        px = QPixmap()
        px.loadFromData(data)
        if not px.isNull():
            return px.scaled(size, size, _KEEP_RATIO, _SMOOTH)
        return None
    try:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        img = img.resize((size, size), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        px = QPixmap()
        px.loadFromData(buf.getvalue())
        return px if not px.isNull() else None
    except Exception:
        return None
