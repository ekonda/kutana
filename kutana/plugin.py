import re
from .handler import Handler, HandlerResponse
from .update import UpdateType
from .backends.vkontakte import VkontaktePluginExtension
from .routers import (
    CommandsRouter, AttachmentsRouter, ListRouter, AnyMessageRouter,
    AnyUnprocessedMessageRouter,
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

    def _get_or_add_router(self, router):
        for r in self._routers:
            if isinstance(r, router):
                return r

        r = router()
        self._routers.append(r)
        return r

    def on_start(self):
        """
        Decorator for registering coroutine to be called when application
        starts. It will be passed an application as an argument.
        """
        def decorator(func):
            if self._on_start is not None:
                raise RuntimeError(f"Hook 'on_start' already set")
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
                raise RuntimeError(f"Hook 'on_before' already set")
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
                raise RuntimeError(f"Hook 'on_after' already set")
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
                raise RuntimeError(f"Hook 'on_exception' already set")
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
                raise RuntimeError(f"Hook 'on_shutdown' already set")
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
        group_state="*",
        user_state="*",
        priority=0,
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

        You can specify group_state and/or user_state to control
        which state must have groups and users attempting to
        access this coroutine.

        Priority is a value that used to determine order in which
        coroutines are executed. If coroutine returns anythign but
        :class:`kutana.handler.HandlerResponse` SKIPPED, other
        coroutines are not executed further.
        """

        if not isinstance(commands, (list, tuple)):
            raise ValueError("`commands` argument must be list or tuple")

        def decorator(func):
            router = self._get_or_add_router(CommandsRouter)
            for command in commands:
                router.add_handler(
                    Handler(func, group_state, user_state, priority),
                    command,
                )
            return func

        return decorator

    def on_attachments(
        self,
        types,
        group_state="*",
        user_state="*",
        priority=0,
    ):
        """
        Decorator for registering coroutine to be called when
        incoming update is message and have at least one
        attachment with one of specified types.

        You can specify group_state and/or user_state to control
        which state must have groups and users attempting to
        access this coroutine.

        Priority is a value that used to determine order in which
        coroutines are executed. If coroutine returns anythign but
        :class:`kutana.handler.HandlerResponse` SKIPPED, other
        coroutines are not executed further.
        """

        def decorator(func):
            router = self._get_or_add_router(AttachmentsRouter)
            for _type in types:
                router.add_handler(
                    Handler(func, group_state, user_state, priority),
                    _type,
                )
            return func

        return decorator

    def on_any_message(self, group_state="*", user_state="*", priority=0):
        """
        Decorator for registering coroutine to be called when
        incoming update is message. This will always be called.
        If you want to catch all unprocessed message, you should
        use :meth:`kutana.plugin.Plugin.on_any_unprocessed_message`.

        You can specify group_state and/or user_state to control
        which state must have groups and users attempting to
        access this coroutine.

        Priority is a value that used to determine order in which
        coroutines are executed. If coroutine returns anythign but
        :class:`kutana.handler.HandlerResponse` SKIPPED, other
        coroutines are not executed further.
        """

        def decorator(func):
            router = self._get_or_add_router(AnyMessageRouter)
            router.add_handler(
                Handler(func, group_state, user_state, priority),
            )
            return func

        return decorator

    def on_any_unprocessed_message(
        self,
        group_state="*",
        user_state="*",
        priority=0,
    ):
        """
        Decorator for registering coroutine to be called when
        incoming update is message. This will be called if no other
        coroutine processed update.

        You can specify group_state and/or user_state to control
        which state must have groups and users attempting to
        access this coroutine.

        Priority is a value that used to determine order in which
        coroutines are executed. If coroutine returns anythign but
        :class:`kutana.handler.HandlerResponse` SKIPPED, other
        coroutines are not executed further.
        """

        def decorator(func):
            router = self._get_or_add_router(AnyUnprocessedMessageRouter)
            router.add_handler(
                Handler(func, group_state, user_state, priority),
            )
            return func

        return decorator

    def on_match(self, pattern, group_state="*", user_state="*", priority=0):
        """
        Decorator for registering coroutine to be called when
        incoming update is message and it's text is matched by
        provided pattern.

        Context is automatically populated with following values:

        - match

        You can specify group_state and/or user_state to control
        which state must have groups and users attempting to
        access this coroutine.

        Priority is a value that used to determine order in which
        coroutines are executed. If coroutine returns anythign but
        :class:`kutana.handler.HandlerResponse` SKIPPED, other
        coroutines are not executed further.
        """

        def decorator(func):
            router = self._get_or_add_router(ListRouter)

            async def wrapper(update, ctx):
                if update.type != UpdateType.MSG:
                    return HandlerResponse.SKIPPED

                match = re.match(pattern, update.text)

                if not match:
                    return HandlerResponse.SKIPPED

                ctx.match = match

                return await func(update, ctx)

            router.add_handler(
                Handler(wrapper, group_state, user_state, priority),
            )

            return wrapper

        return decorator
