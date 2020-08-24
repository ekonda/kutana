import json
import warnings
from ...handler import Handler
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


class ActionMessageRouter(MapRouter):
    __slots__ = ()

    def __init__(self, priority=3):
        """Base priority is 3."""
        super().__init__(priority)

    def add_handler(self, handler, key):
        return super().add_handler(handler, key.lower())

    def _get_keys(self, update, ctx):
        backend_identity = ctx.backend.get_identity()

        if update.type != UpdateType.MSG or backend_identity != "vkontakte":
            return ()

        message = update.raw["object"]["message"]
        if "action" not in message:
            return ()

        action = message["action"]

        ctx.action_type = action["type"]
        ctx.action = action
        return (action["type"],)


class VkontaktePluginExtension:
    def __init__(self, plugin):
        self.plugin = plugin

    def on_payload(self, *args, **kwargs):
        warnings.warn(
            '"on_payload" is deprecated, use "on_payloads" instead',
            DeprecationWarning
        )
        return self.on_payloads(self, *args, **kwargs)

    def on_payloads(
        self,
        payloads,
        priority=0,
        router_priority=None,
    ):
        """
        Decorator for registering coroutine to be called when
        incoming update is message and payload have specified
        content.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and 'router_priority'.
        """

        def decorator(func):
            for payload in payloads:
                self.plugin._add_handler_for_router(
                    PayloadRouter,
                    handler=Handler(func, priority),
                    handler_key=payload,
                    router_priority=router_priority,
                )
            return func

        return decorator

    def on_message_actions(
            self,
            action_types,
            priority=0,
            router_priority=None,
    ):
        """
        Decorator for registering coroutine to be called when
        incoming update is message with action(only for conversations).

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and 'router_priority'.
        """

        def decorator(func):
            for action_type in action_types:
                self.plugin._add_handler_for_router(
                    ActionMessageRouter,
                    handler=Handler(func, priority),
                    handler_key=action_type,
                    router_priority=router_priority,
                )
            return func

        return decorator
