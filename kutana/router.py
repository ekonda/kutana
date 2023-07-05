import re
from typing import List, Dict, Optional

from .context import Context
from .handler import PROCESSED, SKIPPED
from .update import Message


class Router:
    def __init__(self, priority: Optional[int] = 0):
        self.priority = priority

    def add_handler(self, handler):
        raise NotImplementedError

    async def handle(self, update, context):
        raise NotImplementedError

    @staticmethod
    def _assert_can_merge(router, source):
        if type(source) != type(router):
            raise ValueError(f'Mixed routers are passed to "merge" ({source} != {router})')

        if source.priority is None:
            raise ValueError(f'Router with None priority passed to "merge" (it already was merged) ({source})')

    @classmethod
    def merge(cls, source_routers):
        raise NotImplementedError


class ListRouter(Router):
    def __init__(self, priority: Optional[int] = 0):
        super().__init__(priority)
        self._handlers = []

    def add_handler(self, handler):
        self._handlers.append(handler)

    async def handle(self, update, context):
        for handler in self._handlers:
            if isinstance(handler, Router):
                handler = handler.handle

            if await handler(update, context) != SKIPPED:
                return PROCESSED

        return SKIPPED

    @classmethod
    def merge(cls, source_routers: List["ListRouter"]):
        router = cls(priority=None)

        for source in sorted(source_routers, reverse=True, key=lambda item: item.priority or 0):
            cls._assert_can_merge(router, source)

            for handler in source._handlers:
                router.add_handler(handler)

        return router


class MapRouter(Router):
    def __init__(self, priority: Optional[int] = 0):
        super().__init__(priority)
        self._handlers: Dict[str, List] = {}

    def extract_keys(self, context):
        raise NotImplementedError

    def add_handler(self, key, handler):
        if key not in self._handlers:
            self._handlers[key] = []

        self._handlers[key].append(handler)

    async def handle(self, update, context):
        for key in self.extract_keys(context):
            for handler in self._handlers.get(key, ()):
                if isinstance(handler, Router):
                    handler = handler.handle

                if await handler(update, context) != SKIPPED:
                    return PROCESSED

        return SKIPPED

    @staticmethod
    def _merge_routers(target: "MapRouter", source: "MapRouter"):
        for key, handlers in source._handlers.items():
            for handler in handlers:
                target.add_handler(key, handler)

    @classmethod
    def merge(cls, source_routers: List["MapRouter"]):
        router = cls(priority=None)

        for source in sorted(source_routers, reverse=True, key=lambda item: item.priority or 0):
            cls._assert_can_merge(router, source)
            cls._merge_routers(router, source)

        return router


class CommandsRouter(MapRouter):
    def add_handler(self, key, handler):
        return super().add_handler(key.lower(), handler)

    def extract_keys(self, context: Context):
        if not isinstance(context.update, Message):
            return ()

        match = re.match(
            r"\s*({prefix})?\s*({command})(.*)".format(
                prefix="|".join(
                    re.escape(prefix) for prefix in context.app.config["prefixes"]
                ),
                command="|".join(
                    re.escape(command) for command in sorted(self._handlers, key=len, reverse=True)
                ),
            ),
            context.update.text,
            re.IGNORECASE,
        )

        if match is None:
            return ()

        context.prefix = match.group(1)
        context.command = match.group(2)
        context.body = (match.group(3) or "").strip()
        context.match = match

        return (context.command.lower(),)


class AttachmentsRouter(MapRouter):
    def extract_keys(self, context: Context):
        if not isinstance(context.update, Message):
            return ()

        return tuple(attachment.kind for attachment in context.update.attachments)
