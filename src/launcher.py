import os
import subprocess
import webbrowser

from .models import Entry


class EntryLauncher:
    @staticmethod
    def launch(entry: Entry) -> None:
        a = entry.actionable
        dispatch = {
            "exe": EntryLauncher._launch_exe,
            "bat": EntryLauncher._launch_bat,
            "cmd": EntryLauncher._launch_cmd,
            "lnk": EntryLauncher._launch_lnk,
            "ps1": EntryLauncher._launch_ps1,
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
    def _launch_ps1(path: str, args: list, working_dir: str | None) -> None:
        subprocess.Popen(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", path] + args,
            cwd=working_dir,
            close_fds=True,
            creationflags=_DETACHED if os.name == "nt" else 0,
        )

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
