import abc
import weakref
import six
import warnings

try:
    import sortedcontainers
    _HAS_SORTED_CONTAINERS = True
except ImportError:
    warnings.warn("SortedDictPriorityHandlerCollection will not be available, missing sortedcontainers package.")
    _HAS_SORTED_CONTAINERS = False


@six.add_metaclass(abc.ABCMeta)
class HandlerCollection(object):

    @abc.abstractmethod
    def add_handler(self, handler):
        raise NotImplementedError()

    @abc.abstractmethod
    def remove_handler(self, handler):
        raise NotImplementedError()

    @abc.abstractmethod
    def iter_handlers(self):
        raise NotImplementedError()

    def __iadd__(self, handler):
        self.add_handler(handler)
        return self

    def __isub__(self, handler):
        self.remove_handler(handler)
        return self

    def __iter__(self):
        return self.iter_handlers()

    def __getattr__(self, item):
        return getattr(self.handlers, item)


class ListHandlerCollection(HandlerCollection):

    def __init__(self):
        self.handlers = list()

    def add_handler(self, handler):
        self.handlers.append(handler)

    def remove_handler(self, handler):
        self.handlers.remove(handler)

    def iter_handlers(self):
        return iter(self.handlers)


@six.add_metaclass(abc.ABCMeta)
class PriorityHandlerCollection(HandlerCollection):

    @abc.abstractmethod
    def add_handler(self, handler, priority=10):
        raise NotImplementedError()

    def iter_handlers(self):
        for priority, handlers in self.iter_handlers_by_priority():
            for handler in handlers:
                yield handler

    @abc.abstractmethod
    def iter_handlers_by_priority(self):
        raise NotImplementedError()


if _HAS_SORTED_CONTAINERS:
    class SortedDictPriorityHandlerCollection(PriorityHandlerCollection):

        def __init__(self):
            self.map = sortedcontainers.SortedDict()
            self.weakmap = weakref.WeakKeyDictionary()

        def add_handler(self, handler, priority=10):
            if not priority in self.map:
                self.map[priority] = list()
            self.map[priority].append(handler)
            self.weakmap[handler] = priority

        def remove_handler(self, handler):
            priority = self.weakmap.pop(handler)
            self.map[priority].remove(handler)
            if not self.map[priority]:
                del self.map[priority]

        def iter_handlers_by_priority(self):
            return self.map.iteritems()
