from uninhibited.utils import _sentinel
from uninhibited import Event, PriorityEvent


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
    <uninhibited.dispatch.Handler object at ...>

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
    4
    >>> list(d)
    [...]
    """

    create_events_on_access = False
    create_events_on_fire = True

    event_factory = Event
    internal_event_factory = event_factory
    events_mapping_factory = dict
    handlers_container_factory = list

    def __init__(
        self,
        event_names=None,
        create_events_on_access=None,
        create_events_on_fire=None,
        event_factory=None,
        internal_event_factory=None,
        events_mapping_factory=None,
        handlers_container_factory=None
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
        if create_events_on_access is not None:
            self.create_events_on_access = create_events_on_access
        if create_events_on_fire is not None:
            self.create_events_on_fire = create_events_on_fire
        if event_factory:
            self.event_factory = event_factory
        if internal_event_factory:
            self.internal_event_factory = internal_event_factory
        if events_mapping_factory:
            self.events_mapping_factory = events_mapping_factory
        if handlers_container_factory:
            self.handlers_container_factory = handlers_container_factory

        self.handlers = self.handlers_container_factory()
        self.events = self.events_mapping_factory()
        self.clear()

        if event_names:
            # Register given events
            self.add_events(event_names)

    internal_events = ['on_handler_add', 'on_handler_remove', 'on_add_event']

    def _setup_internal_events(self):
        # Register internal events
        self._add_internal_events(self.internal_events)

    def clear(self):
        """
        Clear all handlers and events.
        """
        del self.handlers[:]
        self.events.clear()
        self._setup_internal_events()

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

    def _add_internal_event(self, name, send_event=False, internal_event_factory=None):
        """
        This is only here to ensure my constant hatred for Python 2's horrid variable argument support.
        """
        if not internal_event_factory:
            internal_event_factory = self.internal_event_factory
        return self.add_event(names, send_event=send_event, event_factory=internal_event_factory)

    def _add_internal_events(self, names, send_event=False, internal_event_factory=None):
        if not internal_event_factory:
            internal_event_factory = self.internal_event_factory
        return self.add_events(names, send_event=send_event, event_factory=internal_event_factory)

    def add_events(self, names, send_event=True, event_factory=None):
        """
        Add event by name.

        This is called for you as needed if you allow auto creation of events (see __init__).

        Upon an event being added, all handlers are searched for if they have this event,
        and if they do, they are added to the Event's list of callables.

        :param tuple names: Names
        """
        if not event_factory:
            event_factory = self.event_factory

        # Create events
        self.events.update({name: event_factory() for name in names},)
        # Inspect handlers to see if they should be attached to this new event
        [self._attach_handler_events(handler, events=names) for handler in self.handlers]

        if send_event:
            [self.on_add_event(name) for name in names]

    def add_event(self, name, send_event=True, event_factory=None):
        """
        Add event by name.

        This is called for you as needed if you allow auto creation of events (see __init__).

        Upon an event being added, all handlers are searched for if they have this event,
        and if they do, they are added to the Event's list of callables.

        This is only here to ensure my constant hatred for Python 2's horrid variable argument support.

        :param str|unicode name: Name
        """
        return self.add_events((name,),send_event=send_event,event_factory=event_factory)

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

    def _add(self, handler, allow_dupe=False, send_event=True):
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
        if send_event:
            self.on_handler_add(handler)

    def add(self, handler, allow_dupe=False, send_event=True):
        """
        Add handler instance and attach any events to it.

        :param object handler: handler instance
        :param bool allow_dupe: If True, allow registering a handler more than once.
        :return object: The handler you added is given back so this can be used as a decorator.
        """
        self._add(handler, allow_dupe=allow_dupe, send_event=send_event)
        return handler

    def __iadd__(self, handler):
        """
        Inplace add operator (+=) to add a handler.

        :param object handler: handler instance
        :return Dispatch: self, as required by inplace operators
        """
        self._add(handler)
        return self

    def _remove(self, handler, send_event=True):
        """
        Remove handler instance and detach any methods bound to it from uninhibited.

        :param object handler: handler instance
        :return object: The handler you added is given back so this can be used as a decorator.
        """
        for event in self:
            event.remove_handlers_bound_to_instance(handler)
        self.handlers.remove(handler)
        if send_event:
            self.on_handler_remove(handler)

    def remove(self, handler):
        """
        Remove handler instance and detach any methods bound to it from uninhibited.

        :param object handler: handler instance
        :return object: The handler you added is given back so this can be used as a decorator.
        """
        self._remove(handler)
        return handler

    def __isub__(self, handler):
        """
        Inplace sub operator (+=) to remove a handler.

        :param object handler: handler instance
        :return Dispatch: self, as required by inplace operators
        """
        self._remove(handler)
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
        # for x in self[event].ifire(*args, **kwargs)
        #     yield x
        return self[event].ifire(*args, **kwargs)

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


class PriorityDispatch(Dispatch):
    event_factory = PriorityEvent
    internal_event_factory = PriorityEvent
