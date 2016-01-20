import asyncio
import functools
import inspect
import types

import aitertools

from uninhibited.utils import maybe_async, _sentinel
from uninhibited.events import Event, PriorityEvent
from uninhibited.dispatch import Dispatch


class AsyncMixin:
    pass


class EventFireIter:
    def __init__(self, meth, handlers):
        self._iter = self._iterable(meth, handlers)

    def _iterable(self, meth, handlers):
        return (meth(handler=handler) for handler in handlers)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iter)

    async def __aiter__(self):
        return self

    async def __anext__(self):
        """Fetch the next value from the iterable."""
        try:
            f = next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration() from exc
        return await f


class AsyncEventMixin(AsyncMixin):
    def _call_handler(self, *, handler, args, kwargs, loop=None, start=False, executor=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        if (inspect.iscoroutinefunction(handler) or inspect.isgeneratorfunction(handler)):
            # Get a coro/future
            f = handler(*args, **kwargs)
        else:
            # run_in_executor doesn't support kwargs
            handler = functools.partial(handler, *args, **kwargs)

            # Get result/coro/future
            f = loop.run_in_executor(executor, handler)

        if start:
            # Wrap future in a task, schedule it for execution
            f = asyncio.ensure_future(f, loop=loop)

        # Return a coro that awaits our existing future
        return self._result_tuple(handler, f)

    async def _result_tuple(self, handler, f):
        return handler, await f

    def _results(self, args, kwargs, handlers=_sentinel):
        if handlers is _sentinel:
            handlers = self.handlers

        meth = functools.partial(self._call_handler, args=args, kwargs=kwargs)
        return EventFireIter(meth, handlers)

    def ifire(self, *args, **kwargs):
        fs = self._results(args, kwargs)
        return fs

    def fire(self, *args, **kwargs):
        # Give back the full list of futures, not just the generator
        return self.ifire(*args, **kwargs)

    def ifire_as_completed(self, *args, **kwargs):
        # as_completed requires a list of futures, not a generator, hence fire
        fs = self.fire(*args, **kwargs)
        # returns an iterator of futures that will only resolve once
        return asyncio.as_completed(fs)

    def fire_as_completed(self, *args, **kwargs):
        # Give back the full list of futures, not just the generator
        return list(self.ifire_as_completed(*args, **kwargs))

    def fire_as_completed_gather(self, *args, **kwargs):
        # fs = self.fire(*args, **kwargs)
        fs = self.ifire_as_completed(*args, **kwargs)
        return asyncio.gather(*fs)

    def ifire_wait(self, *args, **kwargs):
        fs = self.ifire(*args, **kwargs)
        return asyncio.wait(fs)

    def ifire_gather(self, *args, **kwargs):
        fs = self.ifire(*args, **kwargs)
        return asyncio.gather(*fs)


class AsyncEvent(AsyncEventMixin, Event):
    pass


class AsyncPriorityEvent(AsyncEventMixin, PriorityEvent):
    pass


class AsyncDispatchMixin(AsyncMixin):
    async def fire_wait(self, event, *args, **kwargs):
        # await ((handler, await f) for handler, f in self.ifire(event, *args, **kwargs))
        results = self.fire(event, *args, **kwargs)
        if not results:
            return
        handlers, fs = zip(*list(results))
        f = await asyncio.wait(fs)
        return results

    async def ifire_wait(self, event, *args, **kwargs):
        results = self.ifire(event, *args, **kwargs)
        handlers, fs = zip(*list(results))
        f = await asyncio.wait(fs)
        return results

    async def ifire_gather(self, event, *args, **kwargs):
        results = self.ifire(event, *args, **kwargs)
        handlers, fs = zip(*list(results))
        f = await asyncio.gather(*fs, return_exceptions=True)
        return results


class AsyncDispatch(AsyncDispatchMixin, Dispatch):
    event_factory = AsyncEvent


class AsyncPriorityDispatch(AsyncDispatchMixin, Dispatch):
    event_factory = AsyncPriorityEvent
