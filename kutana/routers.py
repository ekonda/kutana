import re
from .router import MapRouter, ListRouter
from .update import UpdateType


class CommandsRouter(MapRouter):
    __slots__ = ("_cache",)

    def __init__(self, priority=6):
        """Base priority is 6."""
        super().__init__(priority=priority)
        self._cache = None

    def _populate_cache(self, ctx):
        commands = list(self._handlers.keys())
        prefixes = ctx.config["prefixes"]
        ignore_initial_spaces = ctx.config["ignore_initial_spaces"]

        self._cache = re.compile(
            pattern=r"{spaces_pattern}({prefix}){spaces_pattern}({command})(?:$|\s([\s\S]*))".format(
                prefix="|".join(re.escape(p) for p in prefixes),
                command="|".join(re.escape(c) for c in commands),
                spaces_pattern=r"\s*" if ignore_initial_spaces else "",
            ),
            flags=re.IGNORECASE,
        )

    def add_handler(self, handler, key):
        return super().add_handler(handler, key.lower())

    def _get_keys(self, update, ctx):
        if update.type != UpdateType.MSG:
            return ()

        if self._cache is None:
            self._populate_cache(ctx)

        match = self._cache.match(update.text)

        if match is None:
            return ()

        ctx.prefix = match.group(1)
        ctx.command = match.group(2)
        ctx.body = (match.group(3) or "").strip()
        ctx.match = match

        return (ctx.command.lower(),)


class AttachmentsRouter(MapRouter):
    __slots__ = ()

    def __init__(self, priority=3):
        """Base priority is 3."""
        super().__init__(priority=priority)

    def _get_keys(self, update, ctx):
        if update.type != UpdateType.MSG:
            return ()

        return tuple(a.type for a in update.attachments)


class AnyMessageRouter(ListRouter):
    __slots__ = ()

    def __init__(self, priority=9):
        """Base priority is 9."""
        super().__init__(priority=priority)

    def _check_update(self, update, ctx):
        return update.type == UpdateType.MSG


class AnyUpdateRouter(ListRouter):
    __slots__ = ()

    def __init__(self, priority=9):
        """Base priority is 9."""
        super().__init__(priority=priority)

    def _check_update(self, update, ctx):
        return update.type == UpdateType.UPD
