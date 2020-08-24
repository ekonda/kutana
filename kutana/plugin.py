import re
import warnings
from .handler import Handler, HandlerResponse
from .update import UpdateType
from .backends.vkontakte import VkontaktePluginExtension
from .routers import (
    CommandsRouter, AttachmentsRouter, ListRouter, AnyMessageRouter,
    AnyUpdateRouter
)


class Plugin:
    """
    Plugin provides functionality to the application.

    :param name: Name of the plugin
    :param description: Description of the plugin
    """

    def __init__(self, name, description=""):
        self.name = name
        self.description = description

        self._routers = []

        self._on_start = None
        self._on_before = None
        self._on_after = None
        self._on_exception = None
        self._on_shutdown = None

    def _get_or_add_router(self, router_cls, priority=None):
        for router in self._routers:
            if type(router) == router_cls and (priority is None or priority == router.priority):
                return router

        if priority is None:
            router = router_cls()
        else:
            router = router_cls(priority=priority)

        self._routers.append(router)
        return router

    def _add_handler_for_router(self, router, handler, handler_key=None, router_priority=None):
        router = self._get_or_add_router(router, priority=router_priority)
        if handler_key:
            router.add_handler(handler, handler_key)
        else:
            router.add_handler(handler)

    def on_start(self):
        """
        Decorator for registering coroutine to be called when application
        starts. It will be passed an application as an argument.
        """
        def decorator(func):
            if self._on_start is not None:
                raise RuntimeError("Hook 'on_start' already set")
            self._on_start = func
            return func
        return decorator

    def on_before(self):
        """
        Decorator for registering coroutine to be called before an update
        will be processed. It will be passed the update and it's context as
        arguments.
        """
        def decorator(func):
            if self._on_before is not None:
                raise RuntimeError("Hook 'on_before' already set")
            self._on_before = func
            return func
        return decorator

    def on_after(self):
        """
        Decorator for registering coroutine to be called after an update
        was processed. It will be passed the update, it's context and
        result of processing (:class:`kutana.handler.HandlerResponse`) as
        arguments.
        """
        def decorator(func):
            if self._on_after is not None:
                raise RuntimeError("Hook 'on_after' already set")
            self._on_after = func
            return func
        return decorator

    def on_exception(self):
        """
        Decorator for registering coroutine to be called when exception was
        raised while processing an update. It will be passed the update,
        it's context and raised exception as arguments.
        """
        def decorator(func):
            if self._on_exception is not None:
                raise RuntimeError("Hook 'on_exception' already set")
            self._on_exception = func
            return func
        return decorator

    def on_shutdown(self):
        """
        Decorator for registering coroutine to be called when application
        will be stopped. It will be passed application as an argument.
        """
        def decorator(func):
            if self._on_shutdown is not None:
                raise RuntimeError("Hook 'on_shutdown' already set")
            self._on_shutdown = func
            return func
        return decorator

    # Registrators for updates with specific conditions
    @property
    def vk(self) -> VkontaktePluginExtension:
        return VkontaktePluginExtension(self)

    def on_commands(
        self,
        commands,
        priority=0,
        router_priority=None
    ):
        """
        Decorator for registering coroutine to be called when
        incoming update is message, starts with prefix and one of
        provided commands.

        If case_insensitive is True, commands will be processed with ignored
        case.

        Context is automatically populated with following values:

        - prefix
        - command
        - body
        - match

        Priority is a value that used to determine order in which
        coroutines are executed. Router priority is a value that
        used to determine the order in which routers is checked
        for appropriate handler. By default, most of the times,
        priority is 0, and router_priority is None (default
        value will be used).

        If coroutine returns anythign but
        :class:`kutana.handler.HandlerResponse` SKIPPED, other
        coroutines are not executed further.
        """

        if not isinstance(commands, (list, tuple)):
            raise ValueError("`commands` argument must be list or tuple")

        def decorator(func):
            for command in commands:
                self._add_handler_for_router(
                    CommandsRouter,
                    handler=Handler(func, priority),
                    handler_key=command,
                    router_priority=router_priority,
                )
            return func

        return decorator

    def on_attachments(
        self,
        types,
        priority=0,
        router_priority=None
    ):
        """
        Decorator for registering coroutine to be called when
        incoming update is message and have at least one
        attachment with one of specified types.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and 'router_priority'.
        """

        def decorator(func):
            for atype in types:
                self._add_handler_for_router(
                    AttachmentsRouter,
                    handler=Handler(func, priority),
                    handler_key=atype,
                    router_priority=router_priority,
                )
            return func

        return decorator

    def on_any_message(self, *args, **kwargs):
        warnings.warn(
            '"on_any_message" is deprecated, use "on_messages" instead',
            DeprecationWarning
        )
        return self.on_messages(*args, **kwargs)

    def _make_decorator(self, router, priority, router_priority):
        def decorator(func):
            self._add_handler_for_router(
                router,
                handler=Handler(func, priority),
                router_priority=router_priority,
            )
            return func

        return decorator

    def on_messages(self, priority=0, router_priority=None):
        """
        Decorator for registering coroutine to be called when
        incoming update is message. This will always be called.
        If you want to catch all unprocessed message, you should
        use :meth:`kutana.plugin.Plugin.on_unprocessed_messages`.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and 'router_priority'.
        """

        return self._make_decorator(AnyMessageRouter, priority, router_priority)

    def on_any_unprocessed_message(self, *args, **kwargs):
        warnings.warn(
            '"on_any_unprocessed_message" is deprecated, use "on_unprocessed_messages" instead',
            DeprecationWarning
        )
        return self.on_unprocessed_messages(*args, **kwargs)

    def on_unprocessed_messages(
        self,
        priority=0,
        router_priority=-3
    ):
        """
        Decorator for registering coroutine to be called when
        incoming update is message. This will be called if no other
        coroutine processed update.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and 'router_priority'.
        """

        return self._make_decorator(AnyMessageRouter, priority, router_priority)

    def on_match(self, pattern, priority=0, router_priority=-3):
        """
        Decorator for registering coroutine to be called when
        incoming update is message and it's text is matched by
        provided pattern.

        Context is automatically populated with following values:

        - match

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and 'router_priority'.
        """

        def decorator(func):
            async def wrapper(update, ctx):
                if update.type != UpdateType.MSG:
                    return HandlerResponse.SKIPPED

                match = re.match(pattern, update.text)
                if not match:
                    return HandlerResponse.SKIPPED

                ctx.match = match

                return await func(update, ctx)

            self._add_handler_for_router(
                ListRouter,
                handler=Handler(wrapper, priority),
                router_priority=router_priority,
            )

            return wrapper

        return decorator

    def on_any_update(self, *args, **kwargs):
        warnings.warn(
            '"on_any_update" is deprecated, use "on_updates" instead',
            DeprecationWarning
        )
        return self.on_updates(self, *args, **kwargs)

    def on_updates(self, priority=0, router_priority=None):
        """
        Decorator for registering coroutine to be called when
        incoming update is not message. This will always be called.
        If you want to catch all unprocessed message, you should
        use :meth:`kutana.plugin.Plugin.on_unprocessed_updates`.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and 'router_priority'.
        """

        return self._make_decorator(AnyUpdateRouter, priority, router_priority)

    def on_any_unprocessed_update(self, *args, **kwargs):
        warnings.warn(
            '"on_any_unprocessed_update" is deprecated, use "on_unprocessed_updates" instead',
            DeprecationWarning
        )
        return self.on_unprocessed_updates(self, *args, **kwargs)

    def on_unprocessed_updates(self, priority=0, router_priority=-3):
        """
        Decorator for registering coroutine to be called when
        incoming update is update. This will be called if no other
        coroutine processed update.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and 'router_priority'.
        """

        return self._make_decorator(AnyUpdateRouter, priority, router_priority)
