import types

try:
    import asyncio

    HAS_ASYNCIO = True
except ImportError:
    HAS_ASYNCIO = False

_HAS_ASYNCIO = HAS_ASYNCIO

_sentinel = object()

if HAS_ASYNCIO:

    def maybe_async(value):
        if isinstance(value, (types.CoroutineType, types.GeneratorType, asyncio.Future)):
            return value
        else:
            future = asyncio.Future()
            future.set_result(value)
            return future
