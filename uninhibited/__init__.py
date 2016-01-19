"""
Easy event management.
"""

from uninhibited.events import Event, PriorityEvent
from uninhibited.dispatch import Dispatch, PriorityDispatch

__all__ = ['Event', 'PriorityEvent', 'Dispatch', 'PriorityDispatch']

# Only include async objects if we have asyncio
from uninhibited.utils import _HAS_ASYNCIO

if _HAS_ASYNCIO:
    from uninhibited.async import AsyncEvent, AsyncPriorityEvent, AsyncDispatch, AsyncPriorityDispatch

    __all__.extend(['AsyncEvent', 'AsyncPriorityEvent', 'AsyncDispatch', 'AsyncPriorityDispatch'])
