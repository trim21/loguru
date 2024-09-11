import sys
from sys import exc_info
from types import FrameType
from typing import Callable


def get_frame_fallback(n) -> FrameType | None:
    try:
        raise Exception
    except Exception:
        frame = exc_info()[2].tb_frame.f_back
        for _ in range(n):
            frame = frame.f_back
        return frame


def load_get_frame_function() -> Callable[[int], FrameType | None]:
    if hasattr(sys, "_getframe"):
        get_frame = sys._getframe
    else:
        get_frame = get_frame_fallback
    return get_frame


get_frame = load_get_frame_function()
