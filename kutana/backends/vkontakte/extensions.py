import json
from ...routers import MapRouter
from ...update import UpdateType


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
        priority=0,
        router_priority=None,
    ):
        """
        Decorator for registering coroutine to be called when
        incoming update is message and payload have specified
        content.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'group_state', 'user_state', 'priority' and 'router_priority'.
        """

        def decorator(func):
            for payload in payloads:
                self.plugin._add_handler_for_router(
                    PayloadRouter,
                    handler=self.plugin._make_handler(func, group_state, user_state, priority),
                    handler_key=payload,
                    router_priority=router_priority,
                )
            return func

        return decorator
