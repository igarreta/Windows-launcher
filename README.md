# Windows Launcher

A full-screen overlay app launcher for Windows. Press `Alt+Space` anywhere to bring up a searchable grid of your shortcuts, organized in folders.

## Features

- **Global hotkey** — `Alt+Space` toggles the overlay from anywhere (registered at OS level via `RegisterHotKey`)
- **Icon grid** — Entries displayed as icon tiles with name and description, flowing to fill the screen
- **Folder sidebar** — Vertical list of folders on the right; click to filter the grid
- **Live search** — Type to filter entries across all folders instantly
- **Icon auto-extraction** — Pulls the icon directly from `.exe` and `.lnk` files; also supports custom image files or URLs
- **GUI entry editor** — Add or edit entries through a form dialog (no JSON editing needed)
- **System tray** — Runs in the background; right-click the tray icon to open or quit
- **Supports**: `.exe`, `.bat`, `.cmd`, `.lnk`, `.ps1`, and URLs

## Getting started

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

The app starts minimized to the system tray. Press `Alt+Space` to open the launcher.

## Project structure

```
Windows-launcher/
├── main.py                   # Entry point: tray icon, hotkey, app startup
├── config.json               # Your entries and settings (auto-created if missing)
├── requirements.txt
├── .venv/                    # Virtual environment (not committed)
├── src/
│   ├── models.py             # Dataclasses: Config, Folder, Entry, Actionable, Logo
│   ├── config_manager.py     # Load/save config.json, CRUD helpers
│   ├── launcher.py           # Process spawning for each actionable type
│   ├── icon_resolver.py      # Icon extraction pipeline with disk cache
│   ├── hotkey.py             # RegisterHotKey + QAbstractNativeEventFilter
│   └── ui/
│       ├── main_window.py    # Full-screen frameless overlay
│       ├── folder_sidebar.py # Vertical folder list (right side)
│       ├── icon_grid.py      # Flow-layout grid with filter logic
│       ├── entry_card.py     # Individual icon tile widget
│       ├── entry_editor.py   # Add/edit entry dialog
│       ├── search_bar.py     # Search input
│       └── flow_layout.py    # Custom wrapping QLayout
└── assets/
    └── icons/                # Fallback icons (Qt built-ins used by default)
```

## Configuration

`config.json` is created automatically on first run. You can also edit it directly:

```json
{
  "folders": [
    {
      "id": "dev-tools",
      "name": "Dev Tools",
      "entries": [
        {
          "id": "vscode",
          "name": "VS Code",
          "description": "Code editor",
          "actionable": { "type": "exe", "path": "C:\\...\\Code.exe", "args": [] },
          "logo": { "source": "auto", "value": null }
        }
      ]
    }
  ],
  "settings": {
    "global_hotkey": "Alt+Space",
    "columns": 6
  }
}
```

### Actionable types

| Type | Description |
|------|-------------|
| `exe` | Windows executable — launched directly |
| `bat` | Batch script — run via `cmd /c` |
| `cmd` | Inline command — run via `cmd /c` |
| `lnk` | Windows shortcut — opened via the shell |
| `ps1` | PowerShell script — run with `-ExecutionPolicy Bypass` |
| `url` | Web URL — opened in the default browser |

### Logo sources

| Source | Behaviour |
|--------|-----------|
| `auto` | Extract icon from the target file (exe/lnk); generic icon for URLs |
| `file` | Load an image from a local path (PNG, JPG, ICO, …) |
| `url`  | Download an image from a URL and cache it locally |

## Hotkey registration

The global hotkey is registered with the Windows API (`RegisterHotKey`) so it fires even when the launcher window is hidden. Qt intercepts the resulting `WM_HOTKEY` message via `QAbstractNativeEventFilter` — no background polling thread is needed.

To change the hotkey, edit `"global_hotkey"` in `config.json` and restart the app. Supported modifiers: `Alt`, `Ctrl`, `Win`. Example: `"Ctrl+Alt+L"`.

## Requirements

- Windows 10 / 11
- Python 3.11+
- See `requirements.txt` for Python packages
