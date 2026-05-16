"""Windows Launcher — entry point."""

import sys
import os
import threading
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Qt, QMetaObject
from PySide6.QtGui import QIcon

from src.config_manager import ConfigManager
from src.hotkey import GlobalHotkeyManager
from src.ui.main_window import MainWindow

CONFIG_PATH = Path(__file__).parent / "config.json"


class _Bridge(QObject):
    show_launcher = Signal()
    quit_app = Signal()


def _build_tray_icon(bridge: _Bridge):
    try:
        import pystray
        from PIL import Image, ImageDraw

        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill="#1f6feb")
        draw.rectangle([16, 22, 28, 42], fill="white")
        draw.rectangle([36, 22, 48, 42], fill="white")

        menu = pystray.Menu(
            pystray.MenuItem("Open Launcher", lambda _icon, _item: bridge.show_launcher.emit()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda _icon, _item: bridge.quit_app.emit()),
        )
        icon = pystray.Icon("windows-launcher", img, "Windows Launcher", menu)
        icon.run()
    except Exception as exc:
        print(f"[tray] Failed to start system tray: {exc}", file=sys.stderr)


def main():
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Windows Launcher")
    app.setQuitOnLastWindowClosed(False)

    config_manager = ConfigManager(str(CONFIG_PATH))
    window = MainWindow(config_manager)

    bridge = _Bridge()
    bridge.show_launcher.connect(window.toggle_visibility, Qt.ConnectionType.QueuedConnection)
    bridge.quit_app.connect(app.quit, Qt.ConnectionType.QueuedConnection)

    hotkey_mgr = GlobalHotkeyManager(
        config_manager.config.settings.global_hotkey,
        callback=window.toggle_visibility,
    )
    registered = hotkey_mgr.register(app)
    if not registered and os.name == "nt":
        print("[hotkey] Failed to register global hotkey — may already be in use.", file=sys.stderr)

    tray_thread = threading.Thread(target=_build_tray_icon, args=(bridge,), daemon=True)
    tray_thread.start()

    app.aboutToQuit.connect(lambda: hotkey_mgr.unregister(app))

    exit_code = app.exec()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
