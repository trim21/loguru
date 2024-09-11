""".. |str| replace:: :class:`str`
.. |namedtuple| replace:: :func:`namedtuple<collections.namedtuple>`
.. |dict| replace:: :class:`dict`

.. |Logger| replace:: :class:`~loguru._logger.Logger`
.. |catch| replace:: :meth:`~loguru._logger.Logger.catch()`
.. |contextualize| replace:: :meth:`~loguru._logger.Logger.contextualize()`
.. |complete| replace:: :meth:`~loguru._logger.Logger.complete()`
.. |bind| replace:: :meth:`~loguru._logger.Logger.bind()`
.. |patch| replace:: :meth:`~loguru._logger.Logger.patch()`
.. |opt| replace:: :meth:`~loguru._logger.Logger.opt()`
.. |level| replace:: :meth:`~loguru._logger.Logger.level()`

.. _stub file: https://www.python.org/dev/peps/pep-0484/#stub-files
.. _string literals: https://www.python.org/dev/peps/pep-0484/#forward-references
.. _postponed evaluation of annotations: https://www.python.org/dev/peps/pep-0563/
.. |future| replace:: ``__future__``
.. _future: https://www.python.org/dev/peps/pep-0563/#enabling-the-future-behavior-in-python-3-7
.. |loguru-mypy| replace:: ``loguru-mypy``
.. _loguru-mypy: https://github.com/kornicameister/loguru-mypy
.. |documentation of loguru-mypy| replace:: documentation of ``loguru-mypy``
.. _documentation of loguru-mypy:
    https://github.com/kornicameister/loguru-mypy/blob/master/README.md
.. _@kornicameister: https://github.com/kornicameister

Loguru relies on a `stub file`_ to document its types. This implies that these types are not
accessible during execution of your program, however they can be used by type checkers and IDE.
Also, this means that your Python interpreter has to support `postponed evaluation of annotations`_
to prevent error at runtime. This is achieved with a |future|_ import in Python 3.7+ or by using
`string literals`_ for earlier versions.

A basic usage example could look like this:

.. code-block:: python

    from __future__ import annotations

    import loguru
    from loguru import logger

    def good_sink(message: loguru.Message):
        print("My name is", message.record["name"])

    def bad_filter(record: loguru.Record):
        return record["invalid"]

    logger.add(good_sink, filter=bad_filter)


.. code-block:: bash

    $ mypy test.py
    test.py:8: error: TypedDict "Record" has no key 'invalid'
    Found 1 error in 1 file (checked 1 source file)

There are several internal types to which you can be exposed using Loguru's public API, they are
listed here and might be useful to type hint your code:

- ``Logger``: the usual |logger| object (also returned by |opt|, |bind| and |patch|).
- ``Message``: the formatted logging message sent to the sinks (a |str| with ``record``
  attribute).
- ``Record``: the |dict| containing all contextual information of the logged message.
- ``Level``: the |namedtuple| returned by |level| (with ``name``, ``no``, ``color`` and ``icon``
  attributes).
- ``Catcher``: the context decorator returned by |catch|.
- ``Contextualizer``: the context decorator returned by |contextualize|.
- ``AwaitableCompleter``: the awaitable object returned by |complete|.
- ``RecordFile``: the ``record["file"]`` with ``name`` and ``path`` attributes.
- ``RecordLevel``: the ``record["level"]`` with ``name``, ``no`` and ``icon`` attributes.
- ``RecordThread``: the ``record["thread"]`` with ``id`` and ``name`` attributes.
- ``RecordProcess``: the ``record["process"]`` with ``id`` and ``name`` attributes.
- ``RecordException``: the ``record["exception"]`` with ``type``, ``value`` and ``traceback``
  attributes.

If that is not enough, one can also use the |loguru-mypy|_ library developed by `@kornicameister`_.
Plugin can be installed separately using::

    pip install loguru-mypy

It helps to catch several possible runtime errors by performing additional checks like:

- ``opt(lazy=True)`` loggers accepting only ``typing.Callable[[], typing.Any]`` arguments
- ``opt(record=True)`` loggers wrongly calling log handler like so ``logger.info(..., record={})``
- and even more...

For more details, go to official |documentation of loguru-mypy|_.
"""

import sys
from asyncio import AbstractEventLoop
from collections.abc import Awaitable, Callable, Generator, Sequence
from datetime import time, timedelta
from logging import Handler
from multiprocessing.context import BaseContext
from os import PathLike
from re import Pattern
from types import TracebackType
from typing import (
    Any,
    BinaryIO,
    ContextManager,
    Generic,
    NamedTuple,
    NewType,
    TextIO,
    TypeVar,
    overload,
)

from ._types import Record

if sys.version_info >= (3, 8):
    from typing import Protocol, TypedDict
else:
    from typing_extensions import Protocol, TypedDict

PathLikeStr = PathLike[str]

_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])
ExcInfo = tuple[type[BaseException] | None, BaseException | None, TracebackType | None]

class _GeneratorContextManager(ContextManager[_T], Generic[_T]):
    def __call__(self, func: _F) -> _F: ...
    def __exit__(
        self,
        typ: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

Catcher = NewType("Catcher", _GeneratorContextManager[None])
Contextualizer = NewType("Contextualizer", _GeneratorContextManager[None])
AwaitableCompleter = Awaitable[None]

class Level(NamedTuple):
    name: str
    no: int
    color: str
    icon: str

class Message(str):
    record: Record

class Writable(Protocol):
    def write(self, message: Message) -> None: ...

FilterDict = dict[str | None, str | int | bool]
FilterFunction = Callable[[Record], bool]
FormatFunction = Callable[[Record], str]
PatcherFunction = Callable[[Record], None]
RotationFunction = Callable[[Message, TextIO], bool]
RetentionFunction = Callable[[list[str]], None]
CompressionFunction = Callable[[str], None]

# Actually unusable because TypedDict can't allow extra keys: python/mypy#4617
class _HandlerConfig(TypedDict, total=False):
    sink: str | PathLikeStr | TextIO | Writable | Callable[[Message], None] | Handler
    level: str | int
    format: str | FormatFunction
    filter: str | FilterFunction | FilterDict | None
    colorize: bool | None
    serialize: bool
    backtrace: bool
    diagnose: bool
    enqueue: bool
    catch: bool

class LevelConfig(TypedDict, total=False):
    name: str
    no: int
    color: str
    icon: str

ActivationConfig = tuple[str | None, bool]

class Logger:
    @overload
    def add(
        self,
        sink: TextIO | Writable | Callable[[Message], None] | Handler,
        *,
        level: str | int = ...,
        format: str | FormatFunction = ...,
        filter: str | FilterFunction | FilterDict | None = ...,
        colorize: bool | None = ...,
        serialize: bool = ...,
        backtrace: bool = ...,
        diagnose: bool = ...,
        enqueue: bool = ...,
        context: str | BaseContext | None = ...,
        catch: bool = ...,
    ) -> int: ...
    @overload
    def add(
        self,
        sink: Callable[[Message], Awaitable[None]],
        *,
        level: str | int = ...,
        format: str | FormatFunction = ...,
        filter: str | FilterFunction | FilterDict | None = ...,
        colorize: bool | None = ...,
        serialize: bool = ...,
        backtrace: bool = ...,
        diagnose: bool = ...,
        enqueue: bool = ...,
        context: str | BaseContext | None = ...,
        catch: bool = ...,
        loop: AbstractEventLoop | None = ...,
    ) -> int: ...
    @overload
    def add(
        self,
        sink: str | PathLikeStr,
        *,
        level: str | int = ...,
        format: str | FormatFunction = ...,
        filter: str | FilterFunction | FilterDict | None = ...,
        colorize: bool | None = ...,
        serialize: bool = ...,
        backtrace: bool = ...,
        diagnose: bool = ...,
        enqueue: bool = ...,
        context: str | BaseContext | None = ...,
        catch: bool = ...,
        rotation: str | int | time | timedelta | RotationFunction | None = ...,
        retention: str | int | timedelta | RetentionFunction | None = ...,
        compression: str | CompressionFunction | None = ...,
        delay: bool = ...,
        watch: bool = ...,
        mode: str = ...,
        buffering: int = ...,
        encoding: str = ...,
        **kwargs: Any,
    ) -> int: ...
    def remove(self, handler_id: int | None = ...) -> None: ...
    def complete(self) -> AwaitableCompleter: ...
    @overload
    def catch(
        self,
        exception: type[BaseException] | tuple[type[BaseException], ...] = ...,
        *,
        level: str | int = ...,
        reraise: bool = ...,
        onerror: Callable[[BaseException], None] | None = ...,
        exclude: type[BaseException] | tuple[type[BaseException], ...] | None = ...,
        default: Any = ...,
        message: str = ...,
    ) -> Catcher: ...
    @overload
    def catch(self, function: _F) -> _F: ...
    def opt(
        self,
        *,
        exception: bool | ExcInfo | BaseException | None = ...,
        record: bool = ...,
        lazy: bool = ...,
        colors: bool = ...,
        raw: bool = ...,
        capture: bool = ...,
        depth: int = ...,
        ansi: bool = ...,
    ) -> Logger: ...
    def bind(self, **kwargs: Any) -> Logger: ...
    def contextualize(self, **kwargs: Any) -> Contextualizer: ...
    def patch(self, patcher: PatcherFunction) -> Logger: ...
    @overload
    def level(self, name: str) -> Level: ...
    @overload
    def level(
        self, name: str, no: int = ..., color: str | None = ..., icon: str | None = ...
    ) -> Level: ...
    @overload
    def level(
        self,
        name: str,
        no: int | None = ...,
        color: str | None = ...,
        icon: str | None = ...,
    ) -> Level: ...
    def disable(self, name: str | None) -> None: ...
    def enable(self, name: str | None) -> None: ...
    def configure(
        self,
        *,
        handlers: Sequence[dict[str, Any]] = ...,
        levels: Sequence[LevelConfig] | None = ...,
        extra: dict[Any, Any] | None = ...,
        patcher: PatcherFunction | None = ...,
        activation: Sequence[ActivationConfig] | None = ...,
    ) -> list[int]: ...
    # @staticmethod cannot be used with @overload in mypy (python/mypy#7781).
    # However Logger is not exposed and logger is an instance of Logger
    # so for type checkers it is all the same whether it is defined here
    # as a static method or an instance method.
    @overload
    def parse(
        self,
        file: str | PathLikeStr | TextIO,
        pattern: str | Pattern[str],
        *,
        cast: dict[str, Callable[[str], Any]] | Callable[[dict[str, str]], None] = ...,
        chunk: int = ...,
    ) -> Generator[dict[str, Any], None, None]: ...
    @overload
    def parse(
        self,
        file: BinaryIO,
        pattern: bytes | Pattern[bytes],
        *,
        cast: dict[str, Callable[[bytes], Any]] | Callable[[dict[str, bytes]], None] = ...,
        chunk: int = ...,
    ) -> Generator[dict[str, Any], None, None]: ...
    @overload
    def trace(__self, __message: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: N805
    @overload
    def trace(__self, __message: Any) -> None: ...  # noqa: N805
    @overload
    def debug(__self, __message: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: N805
    @overload
    def debug(__self, __message: Any) -> None: ...  # noqa: N805
    @overload
    def info(__self, __message: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: N805
    @overload
    def info(__self, __message: Any) -> None: ...  # noqa: N805
    @overload
    def success(__self, __message: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: N805
    @overload
    def success(__self, __message: Any) -> None: ...  # noqa: N805
    @overload
    def warning(__self, __message: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: N805
    @overload
    def warning(__self, __message: Any) -> None: ...  # noqa: N805
    @overload
    def error(__self, __message: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: N805
    @overload
    def error(__self, __message: Any) -> None: ...  # noqa: N805
    @overload
    def critical(__self, __message: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: N805
    @overload
    def critical(__self, __message: Any) -> None: ...  # noqa: N805
    @overload
    def exception(__self, __message: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: N805
    @overload
    def exception(__self, __message: Any) -> None: ...  # noqa: N805
    @overload
    def log(self, __level: int | str, __message: str, *args: Any, **kwargs: Any) -> None: ...
    @overload
    def log(self, __level: int | str, __message: Any) -> None: ...
    def start(self, *args: Any, **kwargs: Any) -> int: ...
    def stop(self, *args: Any, **kwargs: Any) -> None: ...

logger: Logger
