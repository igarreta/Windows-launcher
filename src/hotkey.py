import ctypes
import ctypes.wintypes
import os
from typing import Callable

from PySide6.QtCore import QAbstractNativeEventFilter

MOD_ALT = 0x0001
MOD_CTRL = 0x0002
MOD_WIN = 0x0008
VK_SPACE = 0x20
WM_HOTKEY = 0x0312
HOTKEY_ID = 0xBEEF


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_long),
        ("time", ctypes.c_long),
        ("pt_x", ctypes.c_long),
        ("pt_y", ctypes.c_long),
    ]


class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback: Callable):
        super().__init__()
        self._callback = callback

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            try:
                msg = _MSG.from_address(int(message))
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    self._callback()
                    return True, 0
            except Exception:
                pass
        return False, 0


class GlobalHotkeyManager:
    def __init__(self, hotkey_str: str, callback: Callable):
        self._callback = callback
        self._hotkey_str = hotkey_str
        self._filter: HotkeyFilter | None = None
        self._registered = False

    def register(self, app) -> bool:
        if os.name != "nt":
            return False
        try:
            mod, vk = _parse_hotkey(self._hotkey_str)
            result = ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, mod, vk)
            if not result:
                return False
            self._filter = HotkeyFilter(self._callback)
            app.installNativeEventFilter(self._filter)
            self._registered = True
            return True
        except Exception:
            return False

    def unregister(self, app) -> None:
        if self._registered and os.name == "nt":
            try:
                ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
            except Exception:
                pass
        if self._filter:
            app.removeNativeEventFilter(self._filter)
            self._filter = None
        self._registered = False


def _parse_hotkey(hotkey_str: str) -> tuple[int, int]:
    """Parse 'Alt+Space', 'Ctrl+Alt+F1', etc. into (modifiers, vk)."""
    parts = [p.strip() for p in hotkey_str.split("+")]
    mod = 0
    vk = 0
    mod_map = {"alt": MOD_ALT, "ctrl": MOD_CTRL, "control": MOD_CTRL, "win": MOD_WIN}
    vk_map = {
        "space": VK_SPACE,
        **{f"f{i}": 0x6F + i for i in range(1, 13)},
        **{chr(c): c for c in range(ord("A"), ord("Z") + 1)},
    }
    for part in parts:
        lower = part.lower()
        if lower in mod_map:
            mod |= mod_map[lower]
        elif lower in vk_map:
            vk = vk_map[lower]
    return mod, vk
