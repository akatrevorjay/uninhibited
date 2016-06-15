import asyncio
import functools
import inspect

from uninhibited.utils import _sentinel
from uninhibited.events import Event, PriorityEvent
from uninhibited.dispatch import Dispatch


class EventFireIter:
    __slots__ = ('_iter')

    def __init__(self, iterator):
        self._iter = iterator

    def __iter__(self):
        return self

    def next(self):
        return next(self._iter)

    __next__ = next

    async def __aiter__(self):
        return self

    async def anext(self):
        """Fetch the next value from the iterable."""
        try:
            f = next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration() from exc
        return await f

    __anext__ = anext

    async def gather(self):
        fs = self
        return await asyncio.gather(*fs)

    def __await__(self):
        # Voodoo, yes, but this whole PEP is still a bit broken. Sigh.
        return self.gather().__await__()

    def as_completed(self):
        # as_completed requires a list of futures, not a generator
        fs = list(self)
        # returns an iterator of futures that will only resolve once
        iterator = asyncio.as_completed(fs)
        # Return a new instance of this class so you can piggy back .gather or .wait and such
        return self.__class__(iterator)

    async def wait(self):
        fs = self
        return await asyncio.wait(fs)

    def run_until_complete(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        f = self.gather()
        return loop.run_until_complete(f)

    def run_in_executor(self, executor=None, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        # TODO untested
        return loop.run_in_executor(executor, self.run_until_complete)


class AsyncEventMixin:

    def _call_handler(self, *, handler, args, kwargs, loop=None, start=True, executor=None):
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

    def _results(self, args, kwargs, *, handlers=_sentinel, loop=None, start=True, executor=None):
        if handlers is _sentinel:
            handlers = self.handlers

        meth = functools.partial(self._call_handler,
                                 args=args,
                                 kwargs=kwargs,
                                 start=start,
                                 executor=executor,)

        iterator = (meth(handler=handler) for handler in handlers)
        return EventFireIter(iterator)

    """ These are overridden to return our iterator """

    def ifire(self, *args, **kwargs):
        fs = self._results(args, kwargs)
        return fs

    fire = ifire
    __call__ = fire


class AsyncEvent(AsyncEventMixin, Event):
    pass


class AsyncPriorityEvent(AsyncEventMixin, PriorityEvent):
    pass


class AsyncDispatchMixin:

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
