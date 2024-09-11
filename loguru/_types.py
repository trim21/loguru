from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, TypedDict

from ._recattrs import RecordException, RecordFile, RecordLevel, RecordProcess, RecordThread


class Record(TypedDict):
    elapsed: timedelta
    exception: RecordException | None
    extra: dict[Any, Any]
    file: RecordFile
    function: str
    level: RecordLevel
    line: int
    message: str
    module: str
    name: str | None
    process: RecordProcess
    thread: RecordThread
    time: datetime
