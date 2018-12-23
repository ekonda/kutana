"""Structures and classes for plugins."""

import re
from collections import namedtuple

from kutana.functions import done_if_none


Message = namedtuple(
    "Message",
    "text attachments from_id peer_id raw_update"
)

Message.__doc__ = "Text message witch possible attachments."


Attachment = namedtuple(
    "Attachment",
    "type id owner_id access_key link raw_attachment"
)

Attachment.__doc__ = "Detailed information about attachment."


Callbacks = namedtuple(
    "Callbacks",
    "normal raw"
)


class Plugin():
    """Class for creating extensions for kutana engine."""

    def __init__(self, **kwargs):
        self._callbacks = Callbacks([], [])
        self._callbacks_early = Callbacks([], [])

        self._callbacks_special = []

        self._callbacks_dispose = []
        self._callbacks_startup = []

        self.priority = 400

        for k, v in kwargs.items():
            setattr(self, k, v)

    def _prepare_callbacks(self):
        """Return callbacks for registration in executor."""

        callbacks = []

        if self._callbacks_early.normal or self._callbacks_early.raw:

            async def wrapper_for_early(update, env):
                return await self._proc_update(
                    update, env, self._callbacks_early
                )

            wrapper_for_early.priority = self.priority + 200

            callbacks.append(wrapper_for_early)

        if self._callbacks.normal or self._callbacks.raw:

            async def wrapper(update, env):
                return await self._proc_update(
                    update, env, self._callbacks
                )

            wrapper.priority = self.priority

            callbacks.append(wrapper)

        callbacks.extend(self._callbacks_special)

        return callbacks

    @staticmethod
    async def _proc_update(update, env, callbacks):
        """Process update with env and target callbacks.
        If no callbacks passed raises RuntimeException.
        """

        if env.has_message():
            message = env.get_message()

        else:
            message = await env.manager.convert_to_message(update)

            env.set_message(message)

        if message:
            callbacks_type = 0  # callbacks for messages

        else:
            callbacks_type = 1  # callbacks for raw

        inner_env = env.spawn()

        for callback in callbacks[callbacks_type]:
            if callbacks_type == 1:
                res = await callback(update, inner_env)

            else:
                res = await callback(message, inner_env)

            if res == "DONE":
                return "DONE"

    def register(self, *callbacks, early=False):
        """Register for processing updates in this plugin.

        If early is True, this callbacks will be executed
        before callbacks (from other plugins too) with `early=False`.
        """

        if early:
            callbacks_list = self._callbacks_early.normal
        else:
            callbacks_list = self._callbacks.normal

        for callback in callbacks:
            callbacks_list.append(callback)

    def register_special(self, *callbacks, early=False):
        """Register callback for processing updates in this plugins's
        executor. Return decorator for registering callback.

        Arguments raw update and env is passed to callback.

        If `early` is True, this callbacks will be executed
        before callbacks (from other plugins too) with `early=False`.
        """

        def _register_special(callback):
            callback.priority = self.priority + 200 * early

            self._callbacks_special.append(callback)

        for callback in callbacks:
            _register_special(callback)

        return _register_special

    def on_dispose(self):
        """Returns decorator for adding callbacks which is triggered when
        everything is going to shutdown.
        """

        def decorator(coro):
            self._callbacks_dispose.append(coro)

            return coro

        return decorator

    def on_startup(self):
        """Returns decorator for adding callbacks which is triggered
        at the startup of kutana. Decorated coroutine receives update and
        plugin environment (although this env is only accessible in plugin by
        decoraed coroutines).
        """

        def decorator(coro):
            self._callbacks_startup.append(coro)

            return coro

        return decorator

    def on_raw(self, early=False):
        """Returns decorator for adding callbacks which is triggered
        every time when update can't be turned into `Message` or
        `Attachment` object. Arguments raw `update` and `env`
        is passed to callback.

        See :func:`Plugin.register` for info about `early`.
        """

        def decorator(coro):
            async def wrapper(update, env):
                return done_if_none(await coro(update, env))

            if early:
                self._callbacks_early.raw.append(wrapper)

            else:
                self._callbacks.raw.append(wrapper)

            return coro

        return decorator

    def on_text(self, *texts, early=False):
        """Returns decorator for adding callbacks which is triggered
        when the message and any of the specified text are fully matched.

        See :func:`Plugin.register` for info about `early`.
        """

        if not texts:
            raise ValueError("No texts passed to `Plugin.on_text`")

        def decorator(coro):
            check_texts = list(text.strip().lower() for text in texts)

            async def wrapper(message, env):
                if message.text.strip().lower() in check_texts:
                    if done_if_none(await coro(message, env)) == "DONE":
                        return "DONE"

            self.register(wrapper, early=early)

            return wrapper

        return decorator

    def on_has_text(self, *texts, early=False):
        """Returns decorator for adding callbacks which is triggered
        when the message contains any of the specified texts.

        Fills Environment's meta with:

        - "found_text" - text found in message.

        See :func:`Plugin.register` for info about `early`.
        """

        def decorator(coro):
            check_texts = tuple(text.strip().lower() for text in texts) or ("",)

            async def wrapper(message, env):
                check_text = message.text.strip().lower()

                for text in check_texts:
                    if text not in check_text:
                        continue

                    env.meta["found_text"] = text

                    if done_if_none(await coro(message, env)) == "DONE":
                        return "DONE"

            self.register(wrapper, early=early)

            return wrapper

        return decorator

    def on_startswith_text(self, *texts, early=False):
        """Returns decorator for adding callbacks which is triggered
        when the message starts with any of the specified texts.

        Fills Environment's meta with:

        - "body" - text without prefix.
        - "args" - text without prefix splitted in bash-like style.
        - "prefix" - prefix.

        See :func:`Plugin.register` for info about `early`.
        """

        def decorator(coro):
            check_texts = tuple(text.lstrip().lower() for text in texts)

            def search_prefix(message):
                for text in check_texts:
                    if message.startswith(text):
                        return text

                return None

            async def wrapper(message, env):
                search_result = search_prefix(message.text.lower())

                if search_result is None:
                    return

                env.meta["body"] = message.text[len(search_result):].strip()
                env.meta["args"] = env.meta["body"].split()
                env.meta["prefix"] = message.text[:len(search_result)].strip()

                if done_if_none(await coro(message, env)) == "DONE":
                    return "DONE"

            self.register(wrapper, early=early)

            return wrapper

        return decorator

    def on_regexp_text(self, regexp, flags=0, early=False):
        """Returns decorator for adding callbacks which is triggered
        when the message matches the specified regular expression.

        Fills Environment's meta with:

        - "match" - match.

        See :func:`Plugin.register` for info about `early`.
        """

        if isinstance(regexp, str):
            compiled = re.compile(regexp, flags=flags)

        else:
            compiled = regexp

        def decorator(coro):
            async def wrapper(message, env):
                match = compiled.match(message.text)

                if not match:
                    return

                env.meta["match"] = match

                if done_if_none(await coro(message, env)) == "DONE":
                    return "DONE"

            self.register(wrapper, early=early)

            return wrapper

        return decorator

    def on_attachment(self, *types, early=False):
        """Returns decorator for adding callbacks which is triggered
        when the message has attachments of the specified type
        (if no types specified, then any attachments).

        See :func:`Plugin.register` for info about `early`.
        """

        def decorator(coro):
            async def wrapper(message, env):
                attachments = message.attachments

                if not attachments:
                    return

                if types:
                    for a in attachments:
                        if a.type in types:
                            break
                    else:
                        return

                if done_if_none(await coro(message, env)) == "DONE":
                    return "DONE"

            self.register(wrapper, early=early)

            return wrapper

        return decorator
