from __future__ import annotations

import pickle
from types import TracebackType
from typing import Any, NamedTuple, Optional, Type


class RecordLevel:
    __slots__ = ("name", "no", "icon")

    def __init__(self, name: str, no: int, icon: str) -> None:
        self.name: str = name
        self.no: int = no
        self.icon: str = icon

    def __repr__(self) -> str:
        return f"(name={self.name!r}, no={self.no!r}, icon={self.icon!r})"

    def __format__(self, spec: str) -> str:
        return self.name.__format__(spec)


class RecordFile:
    __slots__ = ("name", "path")

    def __init__(self, name: str, path: str) -> None:
        self.name: str = name
        self.path: str = path

    def __repr__(self) -> str:
        return f"(name={self.name!r}, path={self.path!r})"

    def __format__(self, spec: str) -> str:
        return self.name.__format__(spec)


class RecordThread:
    __slots__ = ("id", "name")

    def __init__(self, id_: int, name: str):
        self.id: int = id_
        self.name: str = name

    def __repr__(self) -> str:
        return f"(id={self.id!r}, name={self.name!r})"

    def __format__(self, spec: str) -> str:
        return self.id.__format__(spec)


class RecordProcess:
    __slots__ = ("id", "name")

    def __init__(self, id_: int, name: str):
        self.id: int = id_
        self.name: str = name

    def __repr__(self) -> str:
        return f"(id={self.id!r}, name={self.name!r})"

    def __format__(self, spec: str) -> str:
        return self.id.__format__(spec)


class RecordException(NamedTuple):
    type: Optional[Type[BaseException]]
    value: Optional[BaseException]
    traceback: Optional[TracebackType]

    def __repr__(self) -> str:
        return "(type={!r}, value={!r}, traceback={!r})".format(
            self.type, self.value, self.traceback
        )

    def __reduce__(self) -> Any:
        # The traceback is not picklable, therefore it needs to be removed. Additionally, there's a
        # possibility that the exception value is not picklable either. In such cases, we also need
        # to remove it. This is done for user convenience, aiming to prevent error logging caused by
        # custom exceptions from third-party libraries. If the serialization succeeds, we can reuse
        # the pickled value later for optimization (so that it's not pickled twice). It's important
        # to note that custom exceptions might not necessarily raise a PickleError, hence the
        # generic Exception catch.
        try:
            pickled_value = pickle.dumps(self.value)
        except Exception:
            return (RecordException, (self.type, None, None))
        else:
            return (RecordException._from_pickled_value, (self.type, pickled_value, None))

    @classmethod
    def _from_pickled_value(
        cls,
        type_: Optional[Type[BaseException]],
        pickled_value: bytes,
        traceback_: Optional[TracebackType],
    ) -> "RecordException":
        try:
            # It's safe to use "pickle.loads()" in this case because the pickled value is generated
            # by the same code and is not coming from an untrusted source.
            value = pickle.loads(pickled_value)
        except Exception:
            return cls(type_, None, traceback_)
        else:
            return cls(type_, value, traceback_)
