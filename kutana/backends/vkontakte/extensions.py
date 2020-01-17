import json
from ...routers import MapRouter
from ...update import UpdateType
from ...handler import Handler


class PayloadRouter(MapRouter):
    __slots__ = ()

    def __init__(self, priority=7):
        """Base priority is 7"""
        super().__init__(priority=priority)

    def _to_hashable(self, obj):
        if isinstance(obj, dict):
            return tuple(
                (k, self._to_hashable(v)) for k, v in sorted(obj.items())
            )
        if isinstance(obj, list):
            return tuple(self._to_hashable(o) for o in obj)
        return obj

    def _get_keys(self, update, ctx):
        backend_identity = ctx.backend.get_identity()

        if update.type != UpdateType.MSG or backend_identity != "vkontakte":
            return ()

        message = update.raw["object"]["message"]

        try:
            payload = json.loads(message.get("payload", ""))
        except json.JSONDecodeError:
            return ()

        return (self._to_hashable(payload),)

    def add_handler(self, handler, key):
        return super().add_handler(handler, self._to_hashable(key))


class VkontaktePluginExtension:
    def __init__(self, plugin):
        self.plugin = plugin

    def on_payload(
        self,
        payloads,
        group_state="*",
        user_state="*",
        priority=0
    ):
        """
        Decorator for registering coroutine to be called when
        incoming update is message and payload have specified
        content.

        You can specify group_state and/or user_state to control
        which state must have groups and users attempting to
        access this coroutine.

        Priority is a value that used to determine order in which
        coroutines are executed. If coroutine returns anythign but
        :class:`kutana.handler.HandlerResponse` SKIPPED, other
        coroutines are not executed further.
        """

        def decorator(func):
            router = self.plugin._get_or_add_router(PayloadRouter)
            for payload in payloads:
                router.add_handler(
                    Handler(func, group_state, user_state, priority),
                    payload,
                )
            return func

        return decorator
