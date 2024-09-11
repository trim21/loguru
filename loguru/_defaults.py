from os import environ
from typing import Any, TypeVar

T = TypeVar("T")


def env(key: str, type_: type[T], default: T | None = None) -> Any:
    if key not in environ:
        return default

    val = environ[key]

    if type_ == str:
        return val
    if type_ == bool:
        if val.lower() in ["1", "true", "yes", "y", "ok", "on"]:
            return True
        if val.lower() in ["0", "false", "no", "n", "nok", "off"]:
            return False
        raise ValueError(
            "Invalid environment variable '%s' (expected a boolean): '%s'" % (key, val)
        )
    if type_ == int:
        try:
            return int(val)
        except ValueError:
            raise ValueError(
                "Invalid environment variable '%s' (expected an integer): '%s'" % (key, val)
            ) from None
    raise ValueError("The requested type '%r' is not supported" % type_)


LOGURU_AUTOINIT: bool = env("LOGURU_AUTOINIT", bool, True)

LOGURU_FORMAT: str = env(
    "LOGURU_FORMAT",
    str,
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
LOGURU_FILTER: str = env("LOGURU_FILTER", str, None)
LOGURU_LEVEL: str = env("LOGURU_LEVEL", str, "DEBUG")
LOGURU_COLORIZE: bool = env("LOGURU_COLORIZE", bool, None)
LOGURU_SERIALIZE: bool = env("LOGURU_SERIALIZE", bool, False)
LOGURU_BACKTRACE: bool = env("LOGURU_BACKTRACE", bool, True)
LOGURU_DIAGNOSE: bool = env("LOGURU_DIAGNOSE", bool, True)
LOGURU_ENQUEUE: bool = env("LOGURU_ENQUEUE", bool, False)
LOGURU_CONTEXT: str = env("LOGURU_CONTEXT", str, None)
LOGURU_CATCH: bool = env("LOGURU_CATCH", bool, True)

LOGURU_TRACE_NO: int = env("LOGURU_TRACE_NO", int, 5)
LOGURU_TRACE_COLOR: str = env("LOGURU_TRACE_COLOR", str, "<cyan><bold>")
LOGURU_TRACE_ICON: str = env("LOGURU_TRACE_ICON", str, "\u270F\uFE0F")  # Pencil

LOGURU_DEBUG_NO: int = env("LOGURU_DEBUG_NO", int, 10)
LOGURU_DEBUG_COLOR: str = env("LOGURU_DEBUG_COLOR", str, "<blue><bold>")
LOGURU_DEBUG_ICON: str = env("LOGURU_DEBUG_ICON", str, "\U0001F41E")  # Lady Beetle

LOGURU_INFO_NO: int = env("LOGURU_INFO_NO", int, 20)
LOGURU_INFO_COLOR: str = env("LOGURU_INFO_COLOR", str, "<bold>")
LOGURU_INFO_ICON: str = env("LOGURU_INFO_ICON", str, "\u2139\uFE0F")  # Information

LOGURU_SUCCESS_NO: int = env("LOGURU_SUCCESS_NO", int, 25)
LOGURU_SUCCESS_COLOR: str = env("LOGURU_SUCCESS_COLOR", str, "<green><bold>")
LOGURU_SUCCESS_ICON: str = env("LOGURU_SUCCESS_ICON", str, "\u2705")  # White Heavy Check Mark

LOGURU_WARNING_NO: int = env("LOGURU_WARNING_NO", int, 30)
LOGURU_WARNING_COLOR: str = env("LOGURU_WARNING_COLOR", str, "<yellow><bold>")
LOGURU_WARNING_ICON: str = env("LOGURU_WARNING_ICON", str, "\u26A0\uFE0F")  # Warning

LOGURU_ERROR_NO: int = env("LOGURU_ERROR_NO", int, 40)
LOGURU_ERROR_COLOR: str = env("LOGURU_ERROR_COLOR", str, "<red><bold>")
LOGURU_ERROR_ICON: str = env("LOGURU_ERROR_ICON", str, "\u274C")  # Cross Mark

LOGURU_CRITICAL_NO: int = env("LOGURU_CRITICAL_NO", int, 50)
LOGURU_CRITICAL_COLOR: str = env("LOGURU_CRITICAL_COLOR", str, "<RED><bold>")
LOGURU_CRITICAL_ICON: str = env("LOGURU_CRITICAL_ICON", str, "\u2620\uFE0F")  # Skull and Crossbones
