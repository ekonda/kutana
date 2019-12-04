from sortedcontainers import SortedList
from .handler import HandlerResponse as hr


class Router:
    __slots__ = ("priority",)

    def __init__(self, priority=0):
        self.priority = priority

    def _key(self, handler):
        """Key for sorting handlers."""
        return (
            handler.group_state == "*",
            handler.user_state == "*",
            -handler.priority,
        )

    def _check_update(self, update, ctx):
        """Should update be processed?"""
        return True

    def _check(self, handler, update, ctx):
        """Should this handler handle update?"""

        return (
            (handler.group_state in ("*", ctx.group_state))
            and (handler.user_state in ("*", ctx.user_state))
        )

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
        if not isinstance(other_router, self.__class__):
            raise RuntimeError("Can't merge routers with different classes")

        self._handlers.update(other_router._handlers)

    async def handle(self, update, ctx):
        if not self._check_update(update, ctx):
            return hr.SKIPPED

        for handler in self._handlers:
            if self._check(handler, update, ctx):
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
        if not isinstance(other_router, self.__class__):
            raise RuntimeError("Can't merge routers with different classes")

        for key, handlers in other_router._handlers.items():
            for handler in handlers:
                self.add_handler(handler, key)

    async def handle(self, update, ctx):
        keys = self._get_keys(update, ctx)

        for key in keys:
            if key not in self._handlers:
                continue

            for handler in self._handlers[key]:
                if self._check(handler, update, ctx):
                    if await handler.handle(update, ctx) != hr.SKIPPED:
                        return hr.COMPLETE

        return hr.SKIPPED
