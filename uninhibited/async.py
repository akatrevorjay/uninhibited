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
    def __init__(self, event, handlers, meth):
        self.event = event
        self.handlers = handlers
        self.meth = meth
        self.handlers_iter = iter(self.handlers)

    def __iter__(self):
        return self

    def __next__(self):
        handler = next(self.handlers_iter)
        f = self.meth(handler=handler)
        return f

    async def __aiter__(self):
        return self

    async def __anext__(self):
        """Fetch the next value from the iterable."""
        try:
            handler, f = self.__iter__()
        except StopIteration as exc:
            raise StopAsyncIteration() from exc
        return await f

    def __repr__(self):
        """Get a human representation of the wrapper."""
        cls_name = self.__class__.__name__
        return '<{} event={} handlers={}>'.format(cls_name, self.event, self.handlers)


async def loop_run_executor(meth, *args, executor=None, loop=None):
    if not loop:
        loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, meth, *args)


class AsyncEventMixin(AsyncMixin):
    def _call_handler_orig(self, handler, args, kwargs, loop=None, start=False):
        # TODO Check if it's sync and if so run it in executor
        # Get result/coro/future
        f = super()._call_handler(handler, args, kwargs)

        # Fake non-async callbacks to appear as future
        f = maybe_async(f)

        if start:
            if loop is None:
                loop = asyncio.get_event_loop()

            # Schedule task for execution
            f = asyncio.ensure_future(f, loop=loop)

        return handler, f

    def _call_handler_awaitable(self, *, handler, args, kwargs, loop=None, start=False, executor=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        if not (inspect.isgeneratorfunction(handler) or inspect.iscoroutinefunction(handler)):
            print('Not a coroutinefunction: %s' % handler)

            # run_in_executor doesn't support kwargs
            handler = functools.partial(handler, *args, **kwargs)
            # Get result/coro/future
            f = loop.run_in_executor(executor, handler, *args)
        else:
            # Get result/coro/future
            f = super()._call_handler(handler=handler, args=args, kwargs=kwargs)

        if start:
            # Wrap future in a task, schedule it for execution
            f = asyncio.ensure_future(f, loop=loop)

        # return f
        async def result(handler, f):
            return handler, await f

        ret = result(handler, f)
        # ret = asyncio.wait_for(ret)
        return ret

    _call_handler = _call_handler_awaitable

    async def _call_handler_await(self, *, handler, args, kwargs, loop=None, start=False, executor=None):
        f = self._call_handler(
            handler=handler, args=args, kwargs=kwargs,
            loop=loop, start=start,
            executor=executor,
        )
        return await f

    def _results_async(self, args, kwargs, handlers=_sentinel):
        if handlers is _sentinel:
            handlers = self.handlers

        meth = functools.partial(self._call_handler, args=args, kwargs=kwargs)
        return EventFireIter(self, handlers, meth)

    def _results(self, args, kwargs, handlers=_sentinel):
        if handlers is _sentinel:
            handlers = self.handlers

        meth = functools.partial(self._call_handler, args=args, kwargs=kwargs)
        # return ((h, meth(handler=h)) for h in handlers)
        # return EventFireIter(self, handlers, meth)
        return (meth(handler=h) for h in handlers)

    async def fire(self, *args, **kwargs):
        fs = await self.ifire(*args, **kwargs)
        return await asyncio.gather(*fs)

    async def ifire(self, *args, **kwargs):
        # fs = self._results_async(args, kwargs)
        fs = self._results(args, kwargs)
        fs = list(fs)
        return fs
        # async for handler, result in fs:
        #     return handler, result
        # fs = await aitertools.alist(fs)
        # return await asyncio.gather(*fs)

    async def fire_asc(self, *args, **kwargs):
        fs = await self.ifire(*args, **kwargs)

        f_asc = asyncio.as_completed(fs)
        return f_asc

    async def fire_asc2(self, *args, **kwargs):
        f_asc = await self.fire_asc(*args, **kwargs)
        for f in f_asc:
            handler, result = await f
            print('f_asc: handler=%s result=%s f=%s' % (handler, result, f))
        return await asyncio.gather(*f_asc)

    async def ifire_wait(self, *args, **kwargs):
        results = self.ifire(*args, **kwargs)
        handlers, fs = zip(*list(results))
        f = await asyncio.wait(fs)
        return results

    async def ifire_gather(self, *args, **kwargs):
        results = self.ifire(*args, **kwargs)
        handlers, fs = zip(*list(results))
        f = await asyncio.gather(*fs, return_exceptions=True)
        return results


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
