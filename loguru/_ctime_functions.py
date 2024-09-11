import os
from typing import Callable


def load_ctime_functions() -> tuple[Callable[[str], float], Callable[[str, float], None]]:
    if os.name == "nt":
        import win32_setctime

        def get_ctime_windows(filepath: str) -> float:
            return os.stat(filepath).st_ctime

        def set_ctime_windows(filepath: str, timestamp: float) -> None:
            if not win32_setctime.SUPPORTED:
                return

            try:
                win32_setctime.setctime(filepath, timestamp)
            except (OSError, ValueError):
                pass

        return get_ctime_windows, set_ctime_windows

    if hasattr(os.stat_result, "st_birthtime"):

        def get_ctime_macos(filepath: str) -> float:
            return os.stat(filepath).st_birthtime

        def set_ctime_macos(filepath: str, timestamp: float) -> None:
            pass

        return get_ctime_macos, set_ctime_macos

    if hasattr(os, "getxattr") and hasattr(os, "setxattr"):

        def get_ctime_linux(filepath: str):
            try:
                return float(os.getxattr(filepath, b"user.loguru_crtime"))
            except OSError:
                return os.stat(filepath).st_mtime

        def set_ctime_linux(filepath: str, timestamp: float) -> None:
            try:
                os.setxattr(filepath, b"user.loguru_crtime", str(timestamp).encode("ascii"))
            except OSError:
                pass

        return get_ctime_linux, set_ctime_linux

    def get_ctime_fallback(filepath: str) -> float:
        return os.stat(filepath).st_mtime

    def set_ctime_fallback(filepath: str, timestamp: float) -> None:
        pass

    return get_ctime_fallback, set_ctime_fallback


get_ctime, set_ctime = load_ctime_functions()

__all__ = ["get_ctime", "set_ctime"]
