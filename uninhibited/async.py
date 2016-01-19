import asyncio

from uninhibited.utils import maybe_async
from uninhibited.events import Event, PriorityEvent
from uninhibited.dispatch import Dispatch


class AsyncEventMixin:
    def _call_handler(self, handler, *args, **kwargs):
        # Get result/coro/future
        ret = Event._call_handler(self, handler, *args, **kwargs)
        # Fake non-async callbacks to appear as future
        ret = maybe_async(ret)
        # Wrap coros in Tasks(Futures)
        ret = asyncio.ensure_future(ret)
        return ret


class AsyncEvent(AsyncEventMixin, Event):
    pass


class AsyncPriorityEvent(AsyncEventMixin, PriorityEvent):
    pass


class AsyncDispatchMixin:
    async def fire_wait(self, event, *args, **kwargs):
        # await ((handler, await f) for handler, f in super().ifire(event, *args, **kwargs))
        results = super().fire(event, *args, **kwargs)
        if not results:
            return
        handlers, fs = zip(*list(results))
        f = await asyncio.wait(fs)
        return results

    async def ifire_wait(self, event, *args, **kwargs):
        results = super().ifire(event, *args, **kwargs)
        handlers, fs = zip(*list(results))
        f = await asyncio.wait(fs)
        return results

    async def ifire_gather(self, event, *args, **kwargs):
        results = super().ifire(event, *args, **kwargs)
        handlers, fs = zip(*list(results))
        f = await asyncio.gather(*fs, return_exceptions=True)
        return results


class AsyncDispatch(AsyncDispatchMixin, Dispatch):
    event_factory = AsyncEvent


class AsyncPriorityDispatch(AsyncDispatchMixin, Dispatch):
    event_factory = AsyncPriorityEvent
