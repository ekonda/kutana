import functools
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from .backends.vkontakte import VkontaktePluginExtension
from .context import Context
from .handler import SKIPPED, HandledResultSymbol
from .router import AttachmentsRouter, CommandsRouter, ListRouter, Router
from .storage import Document
from .update import Message

HandlerType = Callable[[Message, Context], Awaitable[Optional[HandledResultSymbol]]]


class Plugin:
    """
    Plugin provides functionality to the application.

    :param name: Name of the plugin
    :param description: Description of the plugin
    """

    def __init__(self, name: str, **kwargs):
        self.app: Any

        self._hooks = []
        self._routers: List[Router] = []

        # Set some attributes to this instance
        self.name = name

        for k, v in kwargs.items():
            setattr(self, k, v)

        # Setup extensions
        self.vk = VkontaktePluginExtension(self)

    def on_start(self):
        """
        Return decorator for registering coroutines that will be called
        when application starts.
        """

        def decorator(coro):
            self._hooks.append(("start", coro))
            return coro

        return decorator

    def on_completion(self):
        """
        Return decorator for registering coroutines that will be called
        after update was processed (without exception).
        """

        def decorator(coro):
            self._hooks.append(("completion", coro))
            return coro

        return decorator

    def on_exception(self):
        """
        Return decorator for registering coroutine that will be called when
        exception was raised while processing an update. It will be passed
        the update's context and raised exception as arguments.
        """

        def decorator(coro):
            self._hooks.append(("exception", coro))
            return coro

        return decorator

    def on_shutdown(self):
        """
        Return decorator for registering coroutine that will be called when
        application is being be stopped.
        """

        def decorator(coro):
            self._hooks.append(("shutdown", coro))
            return coro

        return decorator

    def on_commands(
        self,
        commands: List[str],
        priority: int = 0,
    ):
        """
        Return decorator for registering handler that will be called
        when incoming update is a message, starts with prefix
        and one of provided commands.

        Context is automatically populated with following values:

        - prefix
        - command
        - body
        - match

        Handlers with higher priority are attempted first.

        If handler returns anything but :class:`kutana.handler.SKIPPED`,
        other handlers are not executed further.
        """

        def decorator(coro: HandlerType):
            router = CommandsRouter(priority=priority)
            for command in commands:
                router.add_handler(command, coro)

            self._routers.append(router)

            return coro

        return decorator

    def on_match(
        self,
        patterns: List[Union[str, re.Pattern[str]]],
        priority: int = 0,
    ):
        """
        Return decorator for registering handler that will be called
        when incoming update is a message and it's message matches any
        specified pattern.

        Context is automatically populated with following values:

        - match

        Handlers with higher priority are attempted first.

        If handler returns anything but :class:`kutana.handler.SKIPPED`,
        other handlers are not executed further.
        """

        def decorator(func):
            router = ListRouter(priority=priority)

            @functools.wraps(func)
            async def _wrapper(update, ctx):
                if not isinstance(update, Message):
                    return SKIPPED

                for pattern in patterns:
                    match = re.match(pattern, update.text)
                    if match:
                        break
                else:
                    return SKIPPED

                ctx.match = match

                return await func(update, ctx)

            router.add_handler(_wrapper)

            self._routers.append(router)

            return func

        return decorator

    def on_attachments(
        self,
        kinds: List[str],
        priority: int = 0,
    ):
        """
        Return decorator for registering handler that will be called
        when incoming update is a message and have at least one
        attachment with one of specified types.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and return values.
        """

        def decorator(coro: HandlerType):
            router = AttachmentsRouter(priority=priority)
            for kind in kinds:
                router.add_handler(kind, coro)

            self._routers.append(router)

            return coro

        return decorator

    def on_messages(
        self,
        priority: int = -1,
    ):
        """
        Return decorator for registering handler that will be called
        when incoming update is a message. Handler will always be
        called unless any other handler with lower priority returned
        appropriate value.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and return values.
        """

        def decorator(coro: HandlerType):
            router = ListRouter(priority=priority)

            @functools.wraps(coro)
            async def _wrapper(update, context):
                if not isinstance(update, Message):
                    return SKIPPED
                return await coro(update, context)

            router.add_handler(_wrapper)

            self._routers.append(router)

            return coro

        return decorator

    def on_updates(
        self,
        priority: int = 0,
    ):
        """
        Return decorator for registering handler that will be always
        called (for messages and not messages).

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and return values.
        """

        def decorator(coro: HandlerType):
            router = ListRouter(priority=priority)
            router.add_handler(coro)

            self._routers.append(router)

            return coro

        return decorator

    def with_storage(
        self,
        check_sender: Optional[Dict] = None,
        check_recipient: Optional[Dict] = None,
        storage: str = "default",
    ):
        """
        This decorator allow plugins to implicitly require access to database.
        Context is populated with the following fields:

        - "storage" - Storage object that can be used to get, update or delete
            data, stored with specific keys.
        - "sender" - document with data, previously saved to storage for
            sender of the message.
        - "recipient" - document with data, previously saved to storage for
            recipient of the message.

        This decorator also accepts arguments `check_sender` and `check_recipient`.
        You can specify dictionaries that treated as expected values in corresponding
        data objects. You can use it like `with_storage(check_sender={"state": None})`.
        You can use specific storage by providing "storage" argument.

        Dcoument is an dictionary with additional async methods:

        - "save" - save document's data to database.
        - "update_and_save" - same as "update" and then "save".
        - "reload" - reload data from database.
        - "delete" - deletes data from database.

        Any attempt to save data to database can raise OptimisticLockException, that
        means that your code was working at least partially with outdated data. You
        can either ignore it or retry your operation after reloading data.

        Example:

        .. code-block:: python

            context.sender.update({"field1": "value1"})  # not yet stored in database
            await context.sender.save()  # saves data in database

            context.sender.update_and_save(field2="value2")  # update data and store it in database
        """

        def _perform_check(data: Document, check: Optional[Dict]):
            """Return true if handler should be called."""

            return not check or all(data.get(k) == v for k, v in check.items())

        def decorator(coro: HandlerType):
            @functools.wraps(coro)
            async def wrapper(update, context):
                context.storage = self.app.storages[storage]

                if not getattr(context, "sender", None):
                    context.sender = await context.storage.get(context.sender_unique_id)
                    if not context.sender:
                        context.sender = Document(
                            _storage=context.storage,
                            _storage_key=context.sender_unique_id,
                        )

                if not _perform_check(context.sender, check_sender):
                    return SKIPPED

                if not getattr(context, "recipient", None):
                    context.recipient = await context.storage.get(
                        context.recipient_unique_id
                    )
                    if not context.recipient:
                        context.recipient = Document(
                            _storage=context.storage,
                            _storage_key=context.recipient_unique_id,
                        )

                if not _perform_check(context.recipient, check_recipient):
                    return SKIPPED

                return await coro(update, context)

            return wrapper

        return decorator

    def __getattr__(self, name: str):
        """Defined for typing"""
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value):
        """Defined for typing"""
        return super().__setattr__(name, value)
