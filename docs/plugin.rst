Plugin
======

Description
^^^^^^^^^^^

Plugins allows you to work with incoming updates while abstracting
as much as possible from every concrete controller. You still can
use any specific feature, but you have to know what these features
are. You can specify any amount of callbacks that will process updates
inside of plugin.

Callbacks registration
^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: kutana.Plugin.register

.. automethod:: kutana.Plugin.register_special

Available decorators
^^^^^^^^^^^^^^^^^^^^

.. automethod:: kutana.Plugin.on_text

.. automethod:: kutana.Plugin.on_has_text

.. automethod:: kutana.Plugin.on_startswith_text

.. automethod:: kutana.Plugin.on_regexp_text

.. automethod:: kutana.Plugin.on_attachment

All methods above decorates callback which should look like that:

.. code-block:: python

    async def on_message(message, attachments, env):
        # `message` is instance of Message with text,
        # attachments and update information.

        # `attachments` is tuple of instances of Attachment
        # and update information.

        # `env` is a dictionary (:class:`.objdict`) with data
        # accessible from callbacks of current plugin.
        # `env`.`eenv` is a dictionary (:class:`.objdict`) with
        # data accessible from callbacks of current executor.

        # if you return None or return "DONE", update will
        # be considered successfully processed and its
        # processing will stop. You can return anything but
        # "DONE (for example - "GOON") if you want the update to
        # be processed further.

        pass

.. automethod:: kutana.Plugin.on_startup

.. automethod:: kutana.Plugin.on_raw

.. automethod:: kutana.Plugin.on_dispose

.. note::
  If any callback returns "DONE", no other callback will process this
  update any further. You can return anything but "DONE (for example - "GOON")
  if you want update to be processed further.

Available fields
^^^^^^^^^^^^^^^^

- **priority** - you can manipulate order in which plugins process updates.
  Lower priority - later this plugin will get to process update.  You should
  put often used plugins closer to a beginning as much as possible. You can
  set this value to your callback function. Default value is 45. Plugin's
  early callbacks executed with priority 10 greater than non-early callbacks.


.. note::

    See :ref:`environment` for information about environment
    (`reply`, `upload_doc`, etc.)

    See :ref:`special_updates` for special updates.

Examples
^^^^^^^^

Simple "echo.py"
****************

.. code-block:: python

    from kutana import Plugin

    plugin = Plugin(name="Echo")

    @plugin.on_startswith_text("echo")
    async def on_echo(message, attachments, env):
        await env.reply("{}".format(env.body))

Not quite simple "lister.py"
****************************

.. code-block:: python

    from kutana import Plugin

    plugin = Plugin(name="Plugins")

    @plugin.on_startup()
    async def on_startup(kutana, update):
        plugin.plugins = []  # create list in plugins's memory

        # check all callback owners (possible plugins)
        for pl in update["registered_plugins"]:

            # check if we're working with plugin
            if isinstance(pl, Plugin):

                # save plugin to list
                plugin.plugins.append(pl.name)

    @plugin.on_startswith_text("list")
    async def on_list(message, attachments, env):
        # reply with list of plugins' names
        await env.reply(
            "Plugins:\n" + " | ".join(plugin.plugins)
        )
