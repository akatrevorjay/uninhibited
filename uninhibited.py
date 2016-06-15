"""
Easy event management.
"""
import types

_sentinel = object()


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

    def __init__(self, container_factory=list):
        """
        Init.

        :param callable container_factory: Factory for callback storage; must support append and remove.
        """
        self._handlers = container_factory()

    def add(self, handler):
        """
        Add handler.

        :param callable handler: callable handler
        :return callable: The handler you added is given back so this can be used as a decorator.
        """
        self._handlers.append(handler)
        return handler

    def __iadd__(self, handler):
        """
        Inplace add operator (+=) to add a handler.

        :param callable handler: callable handler
        :return Event: self, as required by inplace operators
        """
        self.add(handler)
        return self

    def remove(self, handler):
        """
        Remove handler.

        :param callable handler: callable handler
        :return callable: The handler you added is given back so this can be used as a decorator.
        """
        self._handlers.remove(handler)
        return handler

    def __isub__(self, handler):
        """
        Inplace sub operator (-=) to remove a handler.

        :param callable handler: callable handler
        :return Event: self, as required by inplace operators
        """
        self.remove(handler)
        return self

    def remove_handlers_bound_to_instance(self, obj):
        """
        Remove all handlers bound to given object instance.
        This is useful to remove all handler methods that are part of an instance.

        :param object obj: Remove handlers that are methods of this instance
        """
        for handler in self:
            if handler.im_self == obj:
                self -= handler

    def fire(self, *args, **kwargs):
        """
        Fire event. call handlers using given arguments, return a list of results.

        :param tuple args: positional arguments to call each handler with
        :param dict kwargs: keyword arguments to call each handler with
        :return list: a list of tuples of handler, return value
        """
        return [(handler, handler(*args, **kwargs)) for handler in self]

    __call__ = fire

    def ifire(self, *args, **kwargs):
        """
        Iteratively fire event, returning generator. Calls each handler using given arguments, upon iteration,
        yielding each result.

        :param tuple args: positional arguments to call each handler with
        :param dict kwargs: keyword arguments to call each handler with
        :return generator: a generator yielding a tuple of handler, return value
        """
        for handler in self:
            yield handler, handler(*args, **kwargs)

    def count(self):
        """
        Return handler count.

        :return int: Number of handlers added
        """
        return len(self._handlers)

    __len__ = count

    def __iter__(self):
        """
        Iterate over handlers.

        :return generator: An iterator over our handlers
        """
        for i in self._handlers:
            yield i

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, list(self._handlers))


class Dispatch(object):
    """
    Manage many events and dispatch them to a number of handlers.

    Handlers are instances that can receive many events via methods named after the event.

    Events are created lazily, and attached to handlers lazily as well.

    Example usage:

    Create instance
    >>> d = Dispatch()

    Define an example event handler:
    >>> class Handler(object):
    ...     def on_echo(self, arg):
    ...         return arg

    Create handler instance:
    >>> handler = Handler()

    Attach handler to our list of handlers:
    >>> d += handler

    You can also use :meth:`add` to do so:
    Duplicates are not allowed by default, unless you specify.
    >>> d.add(handler, allow_dupe=True)

    Fire the event:
    >>> d('on_echo', True)
    [(<bound method Handler.on_echo of ..., True), (<bound method Handler.on_echo of ..., True)]
    >>> d.fire('on_echo', True)
    [(<bound method Handler.on_echo of ..., True), (<bound method Handler.on_echo of ..., True)]

    You can fire the event iteratively via ifire:
    >>> d.ifire('on_echo')  # As you can see it returns a generator
    <generator object ...>
    >>> list(d.ifire('on_echo', False))
    [(<bound method Handler.on_echo of ..., False), (<bound method Handler.on_echo of ..., False)]

    Some introspections are supported:
    >>> len(d)
    1
    >>> list(d)
    ['on_echo']
    """

    def __init__(
        self,
        event_names=None,
        create_events_on_access=False,
        create_events_on_fire=True,
        event_factory=Event,
        events_mapping_factory=dict,
        handlers_container_factory=list
    ):
        """
        Init.

        :param list event_names: List of event names to create on start (optional)
        :param bool create_events_on_access: If True, create event on getitem, eg access.
        :param bool create_events_on_fire: if True, create events on fire.
        :param callable event_factory: Factory to create Event instances
        :param callable events_mapping_factory: Factory to create mapping to store events
        :param callable handlers_container_factory: Factory to create container to store handlers
        """
        self.create_events_on_access = create_events_on_access
        self.create_events_on_fire = create_events_on_fire
        self.event_factory = event_factory

        self.handlers = handlers_container_factory()
        self.events = events_mapping_factory()
        self.clear()

        if event_names:
            self.add_event(*event_names)

    def clear(self):
        """
        Clear all handlers and events.
        """
        del self.handlers[:]
        self.events.clear()

    def get_event(self, name, default=_sentinel):
        """
        Lookup an event by name.

        :param str item: Event name
        :return Event: Event instance under key
        """
        if name not in self.events:
            if self.create_events_on_access:
                self.add_event(name)
            elif default is not _sentinel:
                return default
        return self.events[name]

    def __getitem__(self, item):
        """
        Lookup an event by name via mapping interface.

        :param str item: Event name
        :return Event: Event instance under key
        """
        return self.get_event(item)

    def __getattr__(self, item):
        """
        Lookup an event by name via attribute interface.

        :param str item: Event name
        :return Event: Event instance under key
        """
        return self.get_event(item)

    def __setitem__(self, key, value):
        """
        This is only here to support += on items, so pass.
        """
        pass

    def add_event(self, *names):
        """
        Add event(s) by name.

        This is called for you as needed if you allow auto creation of events (see __init__).

        Upon an event being added, all handlers are searched for if they have this event,
        and if they do, they are added to the Event's list of callables.

        :param tuple names: Names
        """
        for name in names:
            # Create event
            self.events[name] = self.event_factory()
            # Inspect handlers to see if they should be attached to this new event
            for handler in self.handlers:
                self._attach_handler_events(handler, events=[name])

    def _attach_handler_events(self, handler, events=None):
        """
        Search handler for methods named after events, attaching to event handlers as applicable.

        :param object handler: Handler instance
        :param list events: List of event names to look for. If not specified, will do all known event names.
        """
        if not events:
            events = self
        for name in events:
            meth = getattr(handler, name, None)
            if meth:
                self.events[name] += meth

    def add(self, handler, allow_dupe=False):
        """
        Add handler instance and attach any events to it.

        :param object handler: handler instance
        :param bool allow_dupe: If True, allow registering a handler more than once.
        :return object: The handler you added is given back so this can be used as a decorator.
        """
        if not allow_dupe and handler in self.handlers:
            raise ValueError("Handler already present: %s" % handler)
        self.handlers.append(handler)
        self._attach_handler_events(handler)
        return handler

    def __iadd__(self, handler):
        """
        Inplace add operator (+=) to add a handler.

        :param object handler: handler instance
        :return Dispatch: self, as required by inplace operators
        """
        self.add(handler)
        return self

    def remove(self, handler):
        """
        Remove handler instance and detach any methods bound to it from uninhibited.

        :param object handler: handler instance
        :return object: The handler you added is given back so this can be used as a decorator.
        """
        for event in self:
            event.remove_handlers_bound_to_instance(handler)
        self.handlers.remove(handler)
        return handler

    def __isub__(self, handler):
        """
        Inplace sub operator (+=) to remove a handler.

        :param object handler: handler instance
        :return Dispatch: self, as required by inplace operators
        """
        self.remove(handler)
        return self

    def _maybe_create_on_fire(self, event):
        if event in self.events:
            return True
        elif self.create_events_on_fire:
            self.add_event(event)
            return True
        else:
            return False

    def fire(self, event, *args, **kwargs):
        """
        Fire event. call event's handlers using given arguments, return a list of results.

        :param str name: Event name
        :param tuple args: positional arguments to call each handler with
        :param dict kwargs: keyword arguments to call each handler with
        :return list: a list of tuples of handler, return value
        """
        if not self._maybe_create_on_fire(event):
            return
        return self[event].fire(*args, **kwargs)

    __call__ = fire

    def ifire(self, event, *args, **kwargs):
        """
        Iteratively fire event, returning generator. Calls each handler using given arguments, upon iteration,
        yielding each result.

        :param str name: Event name
        :param tuple args: positional arguments to call each handler with
        :param dict kwargs: keyword arguments to call each handler with
        :return generator: a generator yielding a tuple of handler, return value
        """
        if not self._maybe_create_on_fire(event):
            return
        # Wrap the generator per item to force that this method be a generator
        # Python 3.x of course has yield from, which would be great here.
        gen = self[event].ifire(*args, **kwargs)
        for item in gen:
            yield item

    def count(self):
        """
        Return event count.

        :return int: Number of handlers added
        """
        return len(self.events)

    __len__ = count

    def __iter__(self):
        """
        Iterate over event names.

        :return generator: Generator of event names
        """
        return iter(self.events)

    def __repr__(self):
        return '<%s %s handlers=%s>' % (self.__class__.__name__, list(self.events), self.handlers)
