"""Structures and classes for plugins."""

import inspect
import re
from collections import namedtuple


Message = namedtuple(
    "Message",
    "text attachments from_id peer_id date raw_update"
)

Message.__doc__ = """
Text message with possible attachments.

:param text: text message of update
:param attachments: tuple of instances of :class:`.Attachment`
:param from_id: author of sent update (can be None)
:param peer_id: chat identificator or same as from_id (can be None)
:param date: updates's date
:param raw_update: raw update from service
"""


Attachment = namedtuple(
    "Attachment",
    "type id owner_id access_key link raw_attachment"
)

Attachment.__doc__ = """
Detailed information about attachment.

:param type: type of attachment
:param id: attachment's id
:param owner_id: attachment's owner's id
:param access_key: attachment's access key (can be None)
:param link: lint to attachment (can be None)
:param raw_attachment: raw attachment from service
"""


def is_done(value):
    """
    Helper function for deciding if value is sign of successfull
    update's procession.

    :param value: value to interpret
    :rtype: True if value is None or equals to "DONE" otherwise False
    """

    return value is None or value == "DONE"


class Plugin:

    """Class for creating extensions for kutana engine."""

    def __init__(self, **kwargs):
        self._callbacks = []
        self._callbacks_raw = []

        self._callbacks_early = []
        self._callbacks_early_raw = []

        self._callbacks_special = []

        self._callbacks_dispose = []
        self._callbacks_startup = []

        self.priority = 400

        for k, v in kwargs.items():
            setattr(self, k, v)

    def _prepare_callbacks(self):
        """
        Prepare and return callbacks for registration in engine.

        :rtype: list of callbacks to register in engine
        """

        callbacks = []

        if self._callbacks_early or self._callbacks_early_raw:

            async def wrapper_for_early(update, env):
                return await self._proc_update(
                    update, env, early=True
                )

            wrapper_for_early.priority = self.priority + 200

            callbacks.append(wrapper_for_early)

        if self._callbacks or self._callbacks_raw:

            async def wrapper(update, env):
                return await self._proc_update(
                    update, env, early=False
                )

            wrapper.priority = self.priority

            callbacks.append(wrapper)

        callbacks.extend(self._callbacks_special)

        return callbacks

    async def _proc_update(self, update, env, early):
        """
        Process update with env and target callbacks.

        :param update: update to process
        :param env: :class:`.Environment` to process update with
        :param early: process with early callbacks or normal
        :rtype: "DONE" if update is considired updated, None otherwise
        """

        if env.has_message():
            message = env.get_message()

        else:
            message = await env.manager.create_message(update)

            env.set_message(message)

        if early:
            callbacks = [self._callbacks_early, self._callbacks_early_raw]

        else:
            callbacks = [self._callbacks, self._callbacks_raw]

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
        """
        Register for processing updates in this plugin.

        :param callbacks: callbacks for registration in this plugin
        :param early: should callbacks be executed before callbacks (from
            other plugins too) registered with "early=False"
        """

        if early:
            self._callbacks_early.extend(callbacks)

        else:
            self._callbacks.extend(callbacks)

    def register_special(self, *callbacks, early=False):
        """
        Register callback for processing updates in engine directly. Arguments
        raw update and env is passed to callback.

        :param callbacks: callbacks for registration in this plugin
        :param early: should callbacks be executed before callbacks (from
            other plugins too) registered with "early=False"
        :rtype: decorator for registering callback
        """

        def _register_special(callback):
            callback.priority = self.priority + 200 * early

            self._callbacks_special.append(callback)

        for callback in callbacks:
            _register_special(callback)

        return _register_special

    def on_dispose(self):
        """
        Return decorator for adding callbacks which will be triggered when
        everything is going to shutdown.

        :rtype: decorator for adding callbacks
        """

        def decorator(coro):
            self._callbacks_dispose.append(coro)

            return coro

        return decorator

    def on_startup(self):
        """
        Return decorator for adding callbacks which will be triggered
        at the startup of kutana. Decorated coroutine receives update and
        plugin environment.

        :rtype: decorator for adding callbacks
        """

        def decorator(coro):
            self._callbacks_startup.append(coro)

            return coro

        return decorator

    def on_raw(self, early=False):
        """
        Return decorator for adding callback which is triggered
        every time when update can't be turned into :class:`.Message` or
        :class:`.Attachment` object. Arguments raw update and
        :class:`.Environment` is passed to callback.

        :param early: should callbacks be executed before callbacks (from
            other plugins too) registered with "early=False"
        :rtype: decorator for adding callback
        """

        def decorator(coro):
            async def wrapper(update, env):
                if is_done(await coro(update, env)):
                    return "DONE"

            if early:
                self._callbacks_early_raw.append(wrapper)

            else:
                self._callbacks_raw.append(wrapper)

            return coro

        return decorator

    def on_text(self, *texts, early=False):
        """
        Return decorator for adding callback which is triggered
        when the message and any of the specified text are fully matched.

        :param texts: texts to match messages' texts against
        :param early: should callbacks be executed before callbacks (from
            other plugins too) registered with "early=False"
        :rtype: decorator for adding callback
        """

        if not texts:
            raise ValueError('No texts passed to "Plugin.on_text"')

        check_texts = list(text.strip().lower() for text in texts)

        def decorator(coro):
            async def wrapper(message, env):
                if message.text.strip().lower() in check_texts:
                    if is_done(await coro(message, env)):
                        return "DONE"

            self.register(wrapper, early=early)

            return coro

        return decorator

    def on_has_text(self, *texts, early=False):
        """
        Return decorator for adding callback which is triggered
        when the message contains any of the specified texts.

        Keyword argument "found_text" can be passed to callback with the text
        found in message.

        :param texts: texts to search in messages' texts
        :param early: should callbacks be executed before callbacks (from
            other plugins too) registered with "early=False"
        :rtype: decorator for adding callback
        """

        check_texts = tuple(text.strip().lower() for text in texts) or ("",)

        def decorator(coro):
            signature = inspect.signature(coro)

            async def wrapper(msg, env):
                check_text = msg.text.strip().lower()

                if not check_text:
                    return "GOON"

                for text in check_texts:
                    if text not in check_text:
                        continue

                    kwargs = {}

                    if "found_text" in signature.parameters:
                        kwargs["found_text"] = text

                    if is_done(await coro(msg, env, **kwargs)):
                        return "DONE"

            self.register(wrapper, early=early)

            return coro

        return decorator

    def on_startswith_text(self, *texts, early=False):
        """
        Return decorator for adding callbacks which is triggered
        when the message starts with any of the specified texts.

        Keyword arguments "body" (text after prefix), "args" (text after
        prefix splitted by spaces) and "prefix" (text before body) can
        be passed to callback.

        :param texts: texts to search in messages' texts begginngs
        :param early: should callbacks be executed before callbacks (from
            other plugins too) registered with "early=False"
        :rtype: decorator for adding callback
        """

        check_texts = tuple(text.lstrip().lower() for text in texts)

        def decorator(coro):
            signature = inspect.signature(coro)

            def search_prefix(message):
                for text in check_texts:
                    if message.startswith(text):
                        return text

                return None

            async def wrapper(msg, env):
                search_result = search_prefix(msg.text.lower())

                if search_result is None:
                    return

                kwargs = {}

                if "body" in signature.parameters:
                    kwargs["body"] = msg.text[len(search_result):].strip()

                if "args" in signature.parameters:
                    if "body" in kwargs:
                        kwargs["args"] = kwargs["body"].split()

                    else:
                        kwargs["args"] = msg.text[len(search_result):].split()

                if "prefix" in signature.parameters:
                    kwargs["prefix"] = msg.text[:len(search_result)].strip()

                if is_done(await coro(msg, env, **kwargs)):
                    return "DONE"

            self.register(wrapper, early=early)

            return coro

        return decorator

    def on_regexp_text(self, regexp, flags=0, early=False):
        """
        Returns decorator for adding callback which is triggered
        when the message matches the specified regular expression.

        Keyword argument "match" can be passed to callback with
        :class:`re.Match` object for message.

        :param regexp: regular expression to match messages' texts with
        :param flags: flags for :func:`re.compile`
        :param early: should callbacks be executed before callbacks (from
            other plugins too) registered with "early=False"
        :rtype: decorator for adding callback
        """

        if isinstance(regexp, str):
            compiled = re.compile(regexp, flags=flags)

        else:
            compiled = regexp

        def decorator(coro):
            signature = inspect.signature(coro)

            async def wrapper(message, env):
                match = compiled.match(message.text)

                if not match:
                    return

                kwargs = {}

                if "match" in signature.parameters:
                    kwargs["match"] = match

                if is_done(await coro(message, env, **kwargs)):
                    return "DONE"

            self.register(wrapper, early=early)

            return coro

        return decorator

    def on_attachment(self, *types, early=False):
        """
        Returns decorator for adding callback which is triggered
        when the message has attachments of the specified type
        (if no types specified, then any attachments).

        :param types: attachments' types to look for in message
        :param early: should callbacks be executed before callbacks (from
            other plugins too) registered with "early=False"
        :rtype: decorator for adding callback
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

                if is_done(await coro(message, env)):
                    return "DONE"

            self.register(wrapper, early=early)

            return coro

        return decorator
