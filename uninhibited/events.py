from uninhibited import containers
from uninhibited.utils import _sentinel


class Event(object):
    """
    Callback. Register a number of callables and upon fire, it will call each one and return the results.

    Example usage:

    Create instance
    >>> e = Event()

    Define an example callable:
    >>> def echo(arg):
    ...    return arg

    Add the example callable to the event's list of callbacks:
    >>> e += echo

    You can also use :meth:`add` to do so:
    >>> e.add(echo)
    <function echo at ...>

    Fire the event:
    >>> e(True)
    [(<function echo at ...>, True), (<function echo at ...>, True)]
    >>> e.fire(True)
    [(<function echo at ...>, True), (<function echo at ...>, True)]

    You can fire the event iteratively via ifire:
    >>> e.ifire()  # As you can see it returns a generator
    <generator object ...>
    >>> list(e.ifire(False))
    [(<function echo at ...>, False), (<function echo at ...>, False)]

    Some introspections are supported:
    >>> len(e)
    2
    >>> list(e)
    [<function echo at ...>, <function echo at ...>]
    """

    _container_factory = containers.ListHandlerCollection

    def __init__(self, container_factory=None):
        """
        Init.

        :param events.containers.HandlerCollection container_factory: Factory for callback storage; must support append and remove.
        """
        if container_factory:
            self._container_factory = container_factory
        self.container = self._container_factory()

    @property
    def handlers(self):
        return self.container.iter_handlers()

    def add(self, handler):
        """
        Add handler.

        :param callable handler: callable handler
        :return callable: The handler you added is given back so this can be used as a decorator.
        """
        self.container.add_handler(handler)
        return handler

    def __iadd__(self, handler):
        """
        Inplace add operator (+=) to add a handler.

        :param callable handler: callable handler
        :return Event: self, as required by inplace operators
        """
        self.container.add_handler(handler)
        return self

    def remove(self, handler):
        """
        Remove handler.

        :param callable handler: callable handler
        :return callable: The handler you added is given back so this can be used as a decorator.
        """
        self.container.remove_handler(handler)
        return handler

    def __isub__(self, handler):
        """
        Inplace sub operator (-=) to remove a handler.

        :param callable handler: callable handler
        :return Event: self, as required by inplace operators
        """
        self.container.remove_handler(handler)
        return self

    def remove_handlers_bound_to_instance(self, obj):
        """
        Remove all handlers bound to given object instance.
        This is useful to remove all handler methods that are part of an instance.

        :param object obj: Remove handlers that are methods of this instance
        """
        for handler in self.handlers:
            if handler.im_self == obj:
                self -= handler

    def _call_handler(self, handler, args, kwargs):
        return handler(*args, **kwargs)

    def _results(self, args, kwargs, handlers=_sentinel):
        if handlers is _sentinel:
            handlers = self.handlers
        return ((h, self._call_handler(h, args, kwargs)) for h in handlers)

    def fire(self, *args, **kwargs):
        """
        Fire event. call handlers using given arguments, return a list of results.

        :param tuple args: positional arguments to call each handler with
        :param dict kwargs: keyword arguments to call each handler with
        :return list: a list of tuples of handler, return value
        """
        return list(self._results(args, kwargs))

    def ifire(self, *args, **kwargs):
        """
        Iteratively fire event, returning generator. Calls each handler using given arguments, upon iteration,
        yielding each result.

        :param tuple args: positional arguments to call each handler with
        :param dict kwargs: keyword arguments to call each handler with
        :return generator: a generator yielding a tuple of handler, return value
        """
        return self._results(args, kwargs)

    __call__ = fire

    def __len__(self):
        """
        Return handler count.

        :return int: Number of handlers added
        """
        return len(list(self.handlers))

    def __iter__(self):
        """
        Iterate over handlers.

        :return generator: An iterator over our handlers
        """
        return iter(self.handlers)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, list(self.handlers))


class PriorityEvent(Event):
    _container_factory = containers.SortedDictPriorityHandlerCollection

    def add(self, handler, priority=10):
        """
        Add handler.

        :param callable handler: callable handler
        :return callable: The handler you added is given back so this can be used as a decorator.
        """
        self.container.add_handler(handler, priority=priority)
        return handler

    @property
    def handlers_by_priority(self):
        return self.container.iter_handlers_by_priority()

    def ifire_by_priority(self, *args, **kwargs):
        return ((priority, self._results(handlers, args, kwargs)) for priority, handlers in self.handlers_by_priority)

    def fire_by_priority(self, *args, **kwargs):
        return [(priority, list(results)) for priority, results in self.ifire_by_priority(*args, **kwargs)]
