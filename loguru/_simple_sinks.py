from __future__ import annotations

import asyncio
import logging
import weakref
from asyncio import Task, get_running_loop
from collections.abc import Awaitable, Callable, Coroutine
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._error_interceptor import ErrorInterceptor
    from ._handler import Message


class StreamSink:
    def __init__(self, stream: Any) -> None:
        self._stream = stream
        self._flushable = callable(getattr(stream, "flush", None))
        self._stoppable = callable(getattr(stream, "stop", None))
        self._completable = asyncio.iscoroutinefunction(getattr(stream, "complete", None))

    def write(self, message: Message) -> None:
        self._stream.write(message)
        if self._flushable:
            self._stream.flush()

    def stop(self) -> None:
        if self._stoppable:
            self._stream.stop()

    def tasks_to_complete(self) -> list[Awaitable[Any]]:
        if not self._completable:
            return []
        return [self._stream.complete()]


class StandardSink:
    def __init__(self, handler: logging.Handler) -> None:
        self._handler = handler

    def write(self, message: Message) -> None:
        record = message.record
        msg = str(message)
        exc = record["exception"]
        record = logging.getLogger().makeRecord(
            record["name"],
            record["level"].no,
            record["file"].path,
            record["line"],
            msg,
            (),
            (exc.type, exc.value, exc.traceback) if exc else None,
            record["function"],
            {"extra": record["extra"]},
        )
        if exc:
            record.exc_text = "\n"
        self._handler.handle(record)

    def stop(self) -> None:
        self._handler.close()

    def tasks_to_complete(self) -> list[Awaitable[Any]]:
        return []


class AsyncSink:
    def __init__(
        self,
        function: Callable[[Message], Coroutine[Any, Any, None]],
        loop: asyncio.AbstractEventLoop | None,
        error_interceptor: ErrorInterceptor,
    ) -> None:
        self._function = function
        self._loop = loop
        self._error_interceptor = error_interceptor
        self._tasks: weakref.WeakSet[Task[Any]] = weakref.WeakSet()

    def write(self, message: Message) -> None:
        try:
            loop = self._loop or get_running_loop()
        except RuntimeError:
            return

        coroutine = self._function(message)
        task = loop.create_task(coroutine)

        def check_exception(future: Task[Any]) -> None:
            exc = future.exception()
            if future.cancelled() or exc is None:
                return
            if not self._error_interceptor.should_catch():
                raise exc
            self._error_interceptor.print(message.record, exception=exc)

        task.add_done_callback(check_exception)
        self._tasks.add(task)

    def stop(self) -> None:
        for task in self._tasks:
            task.cancel()

    def tasks_to_complete(self) -> list[Awaitable[Any]]:
        # To avoid errors due to "self._tasks" being mutated while iterated, the
        # "tasks_to_complete()" method must be protected by the same lock as "write()" (which
        # happens to be the handler lock). However, the tasks must not be awaited while the lock is
        # acquired as this could lead to a deadlock. Therefore, we first need to collect the tasks
        # to complete, then return them so that they can be awaited outside of the lock.
        return [self._complete_task(task) for task in self._tasks]

    async def _complete_task(self, task: Task[Any]) -> None:
        loop = get_running_loop()
        if task.get_loop() is not loop:
            return
        try:
            await task
        except Exception:
            pass  # Handled in "check_exception()"

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        state["_tasks"] = None
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        self._tasks = weakref.WeakSet()


class CallableSink:
    def __init__(self, function: Callable[[Message], Any]) -> None:
        self._function = function

    def write(self, message: Message) -> None:
        self._function(message)

    def stop(self) -> None:
        pass

    def tasks_to_complete(self) -> list[Awaitable[Any]]:
        return []
