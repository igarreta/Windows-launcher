import os
import subprocess
import threading
import webbrowser
from typing import Callable, Optional

from .models import Entry

# Optional callback used to surface launch results to the user.
# Signature: notifier(title: str, message: str, success: bool)
Notifier = Callable[[str, str, bool], None]


class EntryLauncher:
    _notifier: Optional[Notifier] = None

    @staticmethod
    def set_notifier(notifier: Optional[Notifier]) -> None:
        """Register a callback that receives launch results (e.g. a tray toast)."""
        EntryLauncher._notifier = notifier

    @staticmethod
    def launch(entry: Entry) -> None:
        a = entry.actionable
        # PowerShell scripts run without a console, so we wait for completion in
        # the background and report success/failure through the notifier.
        if a.type == "ps1":
            EntryLauncher._launch_ps1(a.path, a.args, a.working_dir, entry.name)
            return
        dispatch = {
            "exe": EntryLauncher._launch_exe,
            "bat": EntryLauncher._launch_bat,
            "cmd": EntryLauncher._launch_cmd,
            "lnk": EntryLauncher._launch_lnk,
            "url": EntryLauncher._launch_url,
        }
        fn = dispatch.get(a.type)
        if fn is None:
            raise ValueError(f"Unknown actionable type: {a.type}")
        fn(a.path, a.args, a.working_dir)

    @staticmethod
    def _launch_exe(path: str, args: list, working_dir: str | None) -> None:
        subprocess.Popen(
            [path] + args,
            cwd=working_dir,
            close_fds=True,
            creationflags=_DETACHED if os.name == "nt" else 0,
        )

    @staticmethod
    def _launch_bat(path: str, args: list, working_dir: str | None) -> None:
        subprocess.Popen(
            ["cmd", "/c", path] + args,
            cwd=working_dir,
            close_fds=True,
            creationflags=_DETACHED if os.name == "nt" else 0,
        )

    @staticmethod
    def _launch_cmd(path: str, args: list, working_dir: str | None) -> None:
        subprocess.Popen(
            ["cmd", "/c", path] + args,
            cwd=working_dir,
            close_fds=True,
            creationflags=_DETACHED if os.name == "nt" else 0,
        )

    @staticmethod
    def _launch_lnk(path: str, args: list, working_dir: str | None) -> None:
        os.startfile(path)

    @staticmethod
    def _launch_ps1(path: str, args: list, working_dir: str | None, name: str = "") -> None:
        # CREATE_NO_WINDOW (not DETACHED_PROCESS): no console window appears, but
        # we keep the child attached so we can wait for its exit code and capture
        # output. DETACHED_PROCESS silently breaks both.
        proc = subprocess.Popen(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", path] + args,
            cwd=working_dir,
            close_fds=True,
            creationflags=_CREATE_NO_WINDOW if os.name == "nt" else 0,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        label = name or os.path.basename(path)
        threading.Thread(
            target=EntryLauncher._wait_and_notify,
            args=(proc, label),
            daemon=True,
        ).start()

    @staticmethod
    def _wait_and_notify(proc: subprocess.Popen, label: str) -> None:
        try:
            out, _ = proc.communicate()
        except Exception:
            out = ""
        if EntryLauncher._notifier is None:
            return
        ok = proc.returncode == 0
        if ok:
            message = f"{label}: OK (exit 0)"
        else:
            last = next((ln.strip() for ln in reversed((out or "").splitlines()) if ln.strip()), "")
            message = f"{label}: error (exit {proc.returncode})"
            if last:
                message += f"\n{last}"
        try:
            EntryLauncher._notifier("Windows Launcher", message, ok)
        except Exception:
            pass

    @staticmethod
    def _launch_url(path: str, args: list, working_dir: str | None) -> None:
        webbrowser.open(path)

    @staticmethod
    def open_file_location(path: str) -> None:
        if os.name == "nt":
            subprocess.Popen(["explorer", f"/select,{path}"])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path)])


_DETACHED = 0x00000008  # DETACHED_PROCESS on Windows
_CREATE_NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW: no console, but stays waitable
