"""
Easy event management.
"""

from .events import Event, PriorityEvent
from .dispatch import Dispatch, PriorityDispatch

__all__ = ['Event', 'PriorityEvent', 'Dispatch', 'PriorityDispatch']

# Only include async objects if we have asyncio
from .utils import _HAS_ASYNCIO

if _HAS_ASYNCIO:
    from .async import AsyncEvent, AsyncPriorityEvent, AsyncDispatch, AsyncPriorityDispatch

    __all__.extend(['AsyncEvent', 'AsyncPriorityEvent', 'AsyncDispatch', 'AsyncPriorityDispatch'])
