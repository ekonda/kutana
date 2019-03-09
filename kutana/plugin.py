"""Structures and classes for plugins."""

import re
from collections import namedtuple

from .utils import sort_callbacks


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
    :returns: True if value is None or equals to "DONE" otherwise False
    """

    return value is None or value == "DONE"


class Plugin:

    """Class for creating extensions for kutana application."""

    def __init__(self, **kwargs):
        self._callbacks = []
        self._callbacks_raw = []

        self._callback_dispose = None
        self._callback_startup = None

        self.priority = 0

        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_callbacks(self):
        """
        Return callbacks for registration in application.

        :returns: list of callbacks to register in application
        """

        return (self._proc_update,)

    def get_callbacks_for_dispose(self):
        """
        Return dispose callbacks for registration in application.

        :returns: list of callbacks to register in application
        """

        return (self._callback_dispose,) if self._callback_dispose else ()

    def get_callbacks_for_startup(self):
        """
        Return startup callbacks for registration in application.

        :returns: list of callbacks to register in application
        """

        return (self._callback_startup,) if self._callback_startup else ()

    async def _proc_update(self, update, env):
        """
        Process update with env and target callbacks.

        :param update: update to process
        :param env: :class:`.Environment` to process update with
        :returns: "DONE" if update is considired updated, None otherwise
        """

        if env.has_message():
            message = env.get_message()

        else:
            message = await env.manager.create_message(update)

            env.set_message(message)

        callbacks = [self._callbacks, self._callbacks_raw]

        if message:
            callbacks_type = 0  # callbacks for messages

        else:
            callbacks_type = 1  # callbacks for raw

        inner_env = env.spawn()

        for _, callback in callbacks[callbacks_type]:
            res = await callback(message if message else update, inner_env)

            if res == "DONE":
                return "DONE"

    def register(self, *callbacks, priority=0):
        """
        Register for processing updates in this plugin.

        :param callbacks: callbacks for registration in this plugin
        :param priority: priority of callbacks **inside** of this plugin
        """

        for callback in callbacks:
            self._callbacks.append((priority, callback))

        sort_callbacks(self._callbacks)

    def register_raw(self, *callbacks, priority=0):
        """
        Register for processing raw updates in this plugin. These callbacks
        will be used if update can't be converted to :class:`.Message`

        :param callbacks: callbacks for registration in this plugin
        :param priority: priority of callbacks **inside** of this plugin
        """

        for callback in callbacks:
            self._callbacks_raw.append((priority, callback))

        sort_callbacks(self._callbacks_raw)

    def on_dispose(self):
        """
        Return decorator for adding callbacks which will be triggered when
        everything is going to shutdown. Only last registered callback will be
        used.

        :returns: decorator for adding callbacks
        """

        def decorator(coro):
            self._callback_dispose = coro

            return coro

        return decorator

    def on_startup(self):
        """
        Return decorator for adding callbacks which will be triggered
        at the startup of kutana. Decorated coroutine receives
        :class:`.Kutana` application as first argument.
        Only last registered callback will be used.

        :returns: decorator for adding callbacks
        """

        def decorator(coro):
            self._callback_startup = coro

            return coro

        return decorator

    def on_raw(self, priority=0):
        """
        Return decorator for adding callback which is triggered
        every time when update can't be turned into :class:`.Message` or
        :class:`.Attachment` object. Arguments raw update and
        :class:`.Environment` is passed to callback.

        :param priority: priority of callbacks **inside** of this plugin
        :returns: decorator for adding callback
        """

        def decorator(coro):
            async def wrapper(update, env):
                if is_done(await coro(update, env)):
                    return "DONE"

            self.register_raw(wrapper, priority=priority)

            return coro

        return decorator

    def on_text(self, *texts, priority=0):
        """
        Return decorator for adding callback which is triggered
        when the message and any of the specified text are fully matched.

        :param texts: texts to match messages' texts against
        :param priority: priority of callbacks **inside** of this plugin
        :returns: decorator for adding callback
        """

        if not texts:
            raise ValueError('No texts passed to "Plugin.on_text"')

        check_texts = list(text.strip().lower() for text in texts)

        def decorator(coro):
            async def wrapper(message, env):
                if message.text.strip().lower() in check_texts:
                    if is_done(await coro(message, env)):
                        return "DONE"

            self.register(wrapper, priority=priority)

            return coro

        return decorator

    def on_has_text(self, *texts, priority=0):
        """
        Return decorator for adding callback which is triggered
        when the message contains any of the specified texts.

        Environment's additional fields:

        - `found_text` - text found in message.

        :param texts: texts to search in messages' texts or nothing if you
            want callback to be called on any text
        :param priority: priority of callbacks **inside** of this plugin
        :returns: decorator for adding callback
        """

        check_texts = tuple(text.strip().lower() for text in texts) or ("",)

        def decorator(coro):
            async def wrapper(msg, env):
                check_text = msg.text.strip().lower()

                if not check_text:
                    return "GOON"

                for text in check_texts:
                    if text not in check_text:
                        continue

                    env.found_text = text

                    if is_done(await coro(msg, env)):
                        return "DONE"

                    break

            self.register(wrapper, priority=priority)

            return coro

        return decorator

    def on_message(self, priority=0):
        """
        Return decorator for adding callback which is triggered
        when the message exists.

        :param priority: priority of callbacks **inside** of this plugin
        :returns: decorator for adding callback
        """

        def decorator(coro):
            async def wrapper(msg, env):
                if is_done(await coro(msg, env)):
                    return "DONE"

            self.register(wrapper, priority=priority)

            return coro

        return decorator

    def on_startswith_text(self, *texts, priority=0):
        """
        Return decorator for adding callbacks which is triggered
        when the message starts with any of the specified texts.

        Environment's additional fields:

        - `body` - text after prefix.
        - `args` - text after prefix splitted by spaces.
        - `prefix` - text before body.

        :param texts: texts to search in messages' texts begginngs
        :param priority: priority of callbacks **inside** of this plugin
        :returns: decorator for adding callback
        """

        check_texts = tuple(text.lstrip().lower() for text in texts)

        def decorator(coro):
            def search_prefix(message):
                for text in check_texts:
                    if message.startswith(text):
                        return text

                return None

            async def wrapper(msg, env):
                search_result = search_prefix(msg.text.lower())

                if search_result is None:
                    return

                env.body = msg.text[len(search_result):].strip()
                env.args = env.body.split()
                env.prefix = msg.text[:len(search_result)].strip()

                if is_done(await coro(msg, env)):
                    return "DONE"

            self.register(wrapper, priority=priority)

            return coro

        return decorator

    def on_regexp_text(self, regexp, flags=0, priority=0):
        """
        Returns decorator for adding callback which is triggered
        when the message matches the specified regular expression.

        Environment's additional fields:

        - `match` - :class:`re.Match` object for message.

        :param regexp: regular expression to match messages' texts with
        :param flags: flags for :func:`re.compile`
        :param priority: priority of callbacks **inside** of this plugin
        :returns: decorator for adding callback
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

                env.match = match

                if is_done(await coro(message, env)):
                    return "DONE"

            self.register(wrapper, priority=priority)

            return coro

        return decorator

    def on_attachment(self, *types, priority=0):
        """
        Returns decorator for adding callback which is triggered
        when the message has attachments of the specified type
        (if no types specified, then any attachments).

        :param types: attachments' types to look for in message
        :param priority: priority of callbacks **inside** of this plugin
        :returns: decorator for adding callback
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

            self.register(wrapper, priority=priority)

            return coro

        return decorator

    def on_after_processed(self, messages=True, updates=False):
        """
        Returns decorator for adding callback which is triggered
        when the message or update has been processed. If environment contains
        attribute "exception", that means exception was raised while
        other callbacks was processed. This callback has priority 1000000

        Callbacks, registered with `on_after_processed` should not raise
        any exceptions.

        :param messages: call callback for messages
        :param updates: call callback for updates

        :returns: decorator for adding callback
        """

        if not messages and not updates:
            raise ValueError(
                "`messages` or `updates` must be True for `on_after_processed`"
            )

        def decorator(coro):
            async def wrapper(_, env):
                env.parent.register_after_processed(coro)

                return "GOON"

            if messages:
                self.register(wrapper, priority=1000000)

            if updates:
                self.register_raw(wrapper, priority=1000000)

            return coro

        return decorator
