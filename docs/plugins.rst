Plugins
=======

Available methods of :class:`.Plugin` for subscribing to specific updates.

- **on_text(text, ...)** - is triggered when the message and any of the
  specified text are fully matched.
- **on_has_text(text, ...)** - is triggered when the message contains any
  of the specified texts.
- **on_startswith_text(text, ...)** - is triggered when the message starts
  with any of the specified texts.
- **on_regexp_text(regexp, flags = 0)** - is triggered when the message
  matches the specified regular expression.
- **on_attachment(type, ...)** - is triggered when the message has
  attachments of the specified type (if no types specified,
  then any attachments).

All methods above decorates callback which should look like that:

.. code-block:: python

    async def on_message(message, attachments, env, extenv):
        # `message` is instance of Message with text,
        # attachmnets and update information.

        # `attachments` is tuple of instances of Attachment
        # and update information.

        # `env` is a dictionary (:class:`.objdict`) with data
        # accesible from callbacks of current plugin.

        # `extenv` is a dictionary (:class:`.objdict`) with
        # data accesible from callbacks of current executor.

        pass

- **on_startup()** - is triggered at the startup of kutana. Decorated
  coroutine receives kutana object and some information in update. See
  below for example.
- **on_raw()** - is triggered every time when update can't be turned
  into `Message` or `Attachment` object. Arguments `env`, `extenv`
  and raw `update` is passed to callback. If callback returns "DONE", no
  other callback will process this update any further.
- **on_dispose()** - is triggered when everything is going to shutdown.

Available fields of :class:`.Plugin`.

- **order** - you can manipulate order in which plugins process updates.
  Lower value - earlier this plugin will get to process update. This
  works only when using default `load_plugins` function and only inside
  a single call of `load_plugins`. You should put frequently used
  plugins closer to a beginning as much as possible.

See :ref:`special_updates` for special updates.

Examples
********

Simple "echo.py"

.. code-block:: python

    from kutana import Plugin

    plugin = Plugin()

    plugin.name = "Echo"

    @plugin.on_startswith_text("echo")
    async def on_message(message, attachments, env, extenv):
        await env.reply("{}!".format(env.body))

Not quite simple "lister.py"

.. code-block:: python

    from kutana import Plugin, load_plugins

    plugin = Plugin()

    plugin.name = "Plugins Lister"

    @plugin.on_startup()
    async def on_startup(kutana, update):
        plugin.plugins = []  # create list in plugins's memory

        # check all callback owners (possible plugins)
        for pl in update["callbacks_owners"]:

            # check if we're working with plugin
            if isinstance(pl, Plugin):

                # save plugin to list
                plugin.plugins.append(pl.name)

        # read setting from kutana or use default
        plugin.bot_name = kutana.settings.get("bot_name", "noname")

    @plugin.on_startswith_text("list")
    async def on_message(message, attachments, env, extenv):
        # create answer with list of plugins' names and bot name
        await env.reply(
            "Bot with name \"{}\" has:\n".format(plugin.bot_name) +
            "; ".join(plugin.plugins)
        )
