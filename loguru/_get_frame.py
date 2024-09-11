import sys
from sys import exc_info
from types import FrameType
from typing import Callable


def get_frame_fallback(n: int) -> FrameType:
    try:
        raise Exception
    except Exception:
        frame = exc_info()[2].tb_frame.f_back
        for _ in range(n):
            if frame.f_back is None:
                raise Exception("stack not depth enough") from None
            frame = frame.f_back
        return frame


def load_get_frame_function() -> Callable[[int], FrameType]:
    if hasattr(sys, "_getframe"):
        get_frame = sys._getframe
    else:
        get_frame = get_frame_fallback
    return get_frame


get_frame = load_get_frame_function()
