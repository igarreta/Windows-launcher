# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup and running

```powershell
# One-time setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run
python main.py

# Startup registration (writes to HKCU registry, no admin needed)
python main.py --install    # register at login
python main.py --uninstall  # remove
python main.py --status     # check
```

The app starts in the system tray. Press `Alt+Space` to open the overlay.

There is no test suite.

## Architecture

The app is a PySide6 full-screen overlay launcher that stays hidden until the global hotkey fires.

**Data flow:**
- `config.json` is the single source of truth — parsed into `Config → Folder → Entry → Actionable + Logo` dataclasses (`src/models.py`)
- `ConfigManager` (`src/config_manager.py`) owns load/save and all CRUD; all mutations go through it and auto-save
- `MainWindow` receives a `ConfigManager` instance and propagates it to child widgets

**Hotkey:**
- `GlobalHotkeyManager` calls `RegisterHotKey` (Win32 API via `ctypes`) and installs a `QAbstractNativeEventFilter` to intercept `WM_HOTKEY` messages — no polling thread
- Hotkey string is parsed by `_parse_hotkey` in `src/hotkey.py`; supported modifiers: `Alt`, `Ctrl`, `Win`

**Icon resolution pipeline** (`src/icon_resolver.py`):
1. Check `logo.source`: `file` → load path, `url` → download + cache, `auto` → extract from target
2. For `exe`/`bat`/`ps1`/`cmd`: use `icoextract`; for `lnk`: resolve target via `win32com` then extract
3. Cache extracted icons as PNGs under `icon_cache/` (MD5-keyed filenames)
4. Fall back to Qt standard icons by type

**UI components** (`src/ui/`):
- `MainWindow` — frameless, full-screen overlay; shows/hides on hotkey; hosts search bar, icon grid, and folder sidebar
- `IconGrid` — filters `Entry` list by search text and selected folder; wraps `FlowLayout` (custom `QLayout`)
- `EntryCard` — single tile widget; left-click launches via `EntryLauncher`, right-click opens context menu (edit/delete)
- `EntryEditor` — modal dialog for add/edit; talks to `ConfigManager` directly

**Process launching** (`src/launcher.py`): dispatch table by `actionable.type`; all subprocess variants use `DETACHED_PROCESS` flag on Windows so launched apps don't inherit the launcher's console.

**Tray icon**: built with `pystray` + `Pillow` in a daemon thread; communicates back to the Qt event loop via a `QObject` signal bridge (`_Bridge`) with `QueuedConnection` to stay thread-safe.

## Key files

| File | Role |
|---|---|
| `main.py` | Entry point: tray, hotkey wiring, startup registration |
| `src/models.py` | Dataclasses with `to_dict`/`from_dict` for JSON round-trip |
| `src/config_manager.py` | Config CRUD; always call `.save()` after mutations |
| `src/hotkey.py` | Win32 hotkey registration + Qt native event filter |
| `src/icon_resolver.py` | Icon extraction with disk cache |
| `src/launcher.py` | Process spawning per actionable type |
| `src/ui/main_window.py` | Top-level overlay window |

## Windows-specific notes

- `pywin32` (`win32com`) is required for `.lnk` icon resolution; it is installed only on Windows (`sys_platform == "win32"` in requirements)
- `icoextract` is likewise Windows-only
- The `icon_cache/` directory is created at runtime in the working directory (where `main.py` is run from)
- Hotkey registration silently fails on non-Windows platforms (guarded by `os.name != "nt"`)
