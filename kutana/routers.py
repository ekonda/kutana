import re
from .router import MapRouter, ListRouter
from .update import UpdateType


class CommandsRouter(MapRouter):
    __slots__ = ("_pattern", "_pattern_when_mentioned")

    def __init__(self, priority=6):
        """Base priority is 6."""
        super().__init__(priority=priority)
        self._pattern = None
        self._pattern_when_mentioned = None

    def _populate_cache(self, ctx):
        kwargs = {
            "prefix": "|".join(
                re.escape(prefix) for prefix in ctx.config["prefixes"]
            ),
            "mention_prefix": "|".join(
                re.escape(prefix) for prefix in [*ctx.config["prefixes"], *ctx.config["mention_prefix"]]
            ),
            "command": "|".join(
                re.escape(command) for command in list(self._handlers.keys())
            ),
            "spaces": r"\s*" if ctx.config["ignore_initial_spaces"] else "",
        }

        self._pattern = re.compile(
            pattern=r"{spaces}({prefix}){spaces}({command})(?:$|\s([\s\S]*))".format(**kwargs),
            flags=re.IGNORECASE,
        )

        self._pattern_when_mentioned = re.compile(
            pattern=r"{spaces}({prefix}{mention_prefix}){spaces}({command})(?:$|\s([\s\S]*))".format(**kwargs),
            flags=re.IGNORECASE,
        )

    def add_handler(self, handler, key):
        return super().add_handler(handler, key.lower())

    def _get_keys(self, update, ctx):
        if update.type != UpdateType.MSG:
            return ()

        if self._pattern is None:
            self._populate_cache(ctx)

        if update.meta.get("bot_mentioned"):
            match = self._pattern_when_mentioned.match(update.text)
        else:
            match = self._pattern.match(update.text)

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
