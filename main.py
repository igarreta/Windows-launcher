"""Windows Launcher — entry point."""

import sys
import os
import threading
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Qt

from src.config_manager import ConfigManager
from src.hotkey import GlobalHotkeyManager
from src.ui.main_window import MainWindow

CONFIG_PATH = Path(__file__).parent / "config.json"
APP_NAME = "WindowsLauncher"
REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


# ---------------------------------------------------------------------------
# Startup registration (Windows registry, HKCU — no admin rights required)
# ---------------------------------------------------------------------------

def _startup_entry() -> str:
    """Build the command that goes into the registry value."""
    python = Path(sys.executable).resolve()
    script = Path(__file__).resolve()
    # Use pythonw.exe so no console window appears on login
    pythonw = python.parent / "pythonw.exe"
    interpreter = pythonw if pythonw.exists() else python
    return f'"{interpreter}" "{script}"'


def install_autostart() -> None:
    """Register the app to run at Windows login."""
    if os.name != "nt":
        print("Autostart registration is only supported on Windows.")
        return
    import winreg
    cmd = _startup_entry()
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
    print(f"Registered for startup:\n  {cmd}")


def uninstall_autostart() -> None:
    """Remove the app from Windows login startup."""
    if os.name != "nt":
        print("Autostart registration is only supported on Windows.")
        return
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
        print("Removed from startup.")
    except FileNotFoundError:
        print("Not currently registered for startup.")


def check_autostart() -> bool:
    """Return True if the app is registered for startup."""
    if os.name != "nt":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False


# ---------------------------------------------------------------------------
# Tray
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
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
    if "--install" in sys.argv:
        install_autostart()
    elif "--uninstall" in sys.argv:
        uninstall_autostart()
    elif "--status" in sys.argv:
        registered = check_autostart()
        print("Startup: enabled" if registered else "Startup: disabled")
    else:
        main()
