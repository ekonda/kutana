from sortedcontainers import SortedList
from .handler import HandlerResponse as hr


class Router:
    __slots__ = ("priority",)

    def __init__(self, priority=0):
        self.priority = priority

    def _key(self, handler):
        """Key for sorting handlers."""
        return -handler.priority

    def alike(self, other):
        return type(self) is type(other) and self.priority == other.priority

    def _assert_routers_alike(self, other_router):
        if type(other_router) is not type(self):
            raise RuntimeError("Can't merge routers with different classes")

        if other_router.priority != self.priority:
            raise RuntimeError("Can't merge routers with different priorities")

    def _check_update(self, update, ctx):
        """Should update be processed?"""
        return True

    def merge(self, other_router):
        raise NotImplementedError

    async def handle(self, update, ctx):
        raise NotImplementedError


class ListRouter(Router):
    __slots__ = ("_handlers",)

    def __init__(self, priority=0):
        super().__init__(priority)
        self._handlers = SortedList([], key=self._key)

    def add_handler(self, handler):
        self._handlers.add(handler)

    def merge(self, other_router):
        self._assert_routers_alike(other_router)
        self._handlers.update(other_router._handlers)

    async def handle(self, update, ctx):
        if not self._check_update(update, ctx):
            return hr.SKIPPED

        for handler in self._handlers:
            if await handler.handle(update, ctx) != hr.SKIPPED:
                return hr.COMPLETE

        return hr.SKIPPED


class MapRouter(Router):
    __slots__ = ("_handlers",)

    def __init__(self, priority=0):
        super().__init__(priority)
        self._handlers = {}

    def _get_keys(self, update, ctx):
        """
        Returns tuple of strings for determining handlers in `_handlers`
        dictionary.
        """
        raise NotImplementedError

    def add_handler(self, handler, key):
        if key in self._handlers:
            self._handlers[key].add(handler)
        else:
            self._handlers[key] = SortedList([handler], key=self._key)

    def merge(self, other_router):
        self._assert_routers_alike(other_router)

        for key, handlers in other_router._handlers.items():
            for handler in handlers:
                self.add_handler(handler, key)

    async def handle(self, update, ctx):
        keys = self._get_keys(update, ctx)

        for key in keys:
            if key not in self._handlers:
                continue

            for handler in self._handlers[key]:
                if await handler.handle(update, ctx) != hr.SKIPPED:
                    return hr.COMPLETE

        return hr.SKIPPED
