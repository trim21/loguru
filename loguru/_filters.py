from typing import Literal

from ._types import Record


def filter_none(record: Record) -> bool:
    return record["name"] is not None


def filter_by_name(record: Record, parent: str, length: int) -> bool:
    name = record["name"]
    if name is None:
        return False

    name = name + "."
    return name[:length] == parent


def filter_by_level(
    record: Record, level_per_module: dict[str | None, int | Literal[False]]
) -> bool:
    name = record["name"]

    while True:
        level = level_per_module.get(name)
        if level is False:
            return False
        if level is not None:
            return record["level"].no >= level
        if not name:
            return True
        index = name.rfind(".")
        name = name[:index] if index != -1 else ""
