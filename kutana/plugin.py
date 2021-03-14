import re
import inspect
import warnings
import functools
from .handler import Handler, HandlerResponse
from .update import UpdateType
from .helpers import ensure_list
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

    def __init__(self, name, description="", storage="default", **kwargs):
        self.app = None
        self.name = name
        self.description = description

        self._routers = []
        self._storage = storage
        self._handlers = {
            "start": [],
            "before": [],
            "after": [],
            "exception": [],
            "shutdown": [],
        }

        # Set provided attributes to this instance
        for k, v in kwargs.items():
            setattr(self, k, v)

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

    @property
    def storage(self):
        if isinstance(self._storage, str):
            return self.app.get_storage(self._storage)
        return self._storage

    def on_start(self, priority=0):
        """
        Decorator for registering coroutine to be called when application
        starts.

        Priority specifies the order in which handlers are  executed. Handlers
        with higher priority will be executed first.
        """
        def decorator(func):
            async def wrapper():
                args, *__ = inspect.getfullargspec(func)

                if args:
                    warnings.warn(
                        '"on_start" with arguments is deprecated, you can '
                        'access "app" with "plugin.app"',
                        DeprecationWarning
                    )
                    return await func(self.app)
                else:
                    return await func()

            self._handlers["start"].append(Handler(wrapper, priority))

            return func
        return decorator

    def on_before(self, priority=0):
        """
        Decorator for registering coroutine to be called before an update
        will be processed. It will be passed the update and it's context as
        arguments.

        Priority specifies the order in which handlers are executed. Handlers
        with higher priority will be executed first.
        """
        def decorator(func):
            self._handlers["before"].append(Handler(func, priority))
            return func
        return decorator

    def on_after(self, priority=0):
        """
        Decorator for registering coroutine to be called after an update
        was processed. It will be passed the update, it's context and
        result of processing (:class:`kutana.handler.HandlerResponse`) as
        arguments.

        Priority specifies the order in which handlers are executed. Handlers
        with higher priority will be executed first.
        """
        def decorator(func):
            self._handlers["after"].append(Handler(func, priority))
            return func
        return decorator

    def on_exception(self, priority=0):
        """
        Decorator for registering coroutine to be called when exception was
        raised while processing an update. It will be passed the update,
        it's context and raised exception as arguments.

        Priority specifies the order in which handlers are executed. Handlers
        with higher priority will be executed first.
        """
        def decorator(func):
            self._handlers["exception"].append(Handler(func, priority))
            return func
        return decorator

    def on_shutdown(self, priority=0):
        """
        Decorator for registering coroutine to be called when application
        will be stopped. It will be passed application as an argument.

        Priority specifies the order in which handlers are executed. Handlers
        with higher priority will be executed first.
        """
        def decorator(func):
            self._handlers["shutdown"].append(Handler(func, priority))
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

        commands = ensure_list(commands)

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

        types = ensure_list(types)

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

            return func

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

    def expect_sender(self, state=None, localized=False):
        """
        This decorator does following things:

        - It adds 'sender' to the context. Object that contains data you
            previously saved to it. You can treat it as object or dict
            with data. In order to save your changes, you should await
            'save' method (or use 'update').

        - If you specified 'state', this will skip all users that don't have
            specified value in 'state' field.

        - If you 'localized' is true, state will be limited only to current
            receiver.

        NOTE:
            If you will attempt to update state, but between reading and
            writing (updating) someone already updated it 'OptimisticLockException'
            will be raised. By default this exceptions are ignored!
        """

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(upd, ctx, *args, **kwargs):
                sender = await self.storage.get(ctx.sender_key)

                if not sender or "state" not in sender:
                    sender = self.storage.make_document(
                        {"state": "", "_version": None}, ctx.sender_key
                    )

                if state is not None and sender["state"] != state:
                    return HandlerResponse.SKIPPED

                ctx.sender = sender

                return await func(upd, ctx, *args, **kwargs)
            return wrapper
        return decorator

    def expect_receiver(self, state=None):
        """
        This decorator does following things:

        - It adds 'receiver' to the context. Object that contains data you
            previously saved to it. You can treat it as object or dict
            with data. In order to save your changes, you should await
            'save' method (or use 'update').

        NOTE:
            If you will attempt to update state, but between reading and
            writing (updating) someone already updated it - 'OptimisticLockException'
            will be raised. By default this exceptions are ignored!
        """

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(upd, ctx, *args, **kwargs):
                receiver = await self.storage.get(ctx.receiver_key)

                if not receiver or "state" not in receiver:
                    receiver = self.storage.make_document(
                        {"state": "", "_version": None}, ctx.receiver_key
                    )

                if state is not None and receiver["state"] != state:
                    return HandlerResponse.SKIPPED

                ctx.receiver = receiver

                return await func(upd, ctx, *args, **kwargs)
            return wrapper
        return decorator
