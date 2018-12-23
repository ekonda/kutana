====================
Kutana documentation
====================

.. image:: _static/kutana-logo-512.png
    :alt: Kutana
    :scale: 60%

The engine for developing bots for soc. networks,
instant messengers and other systems.

.. note::
    We apologize in advance for errors and omissions in this documentation.
    If you can help improve the documentation corrections or modifications,
    we will be very grateful.

====================
Kutana documentation
====================

Overview
--------
Kutana is a engine for developing bots for social networks, messengers and
other services. Kutana heavily uses asyncio and coroutines. It supports
different backends (like vk.com, telegram.org etc.) throught different
managers.

Workflow
--------
Managers is responsible for receiving and sending data. While data is prepared
(turned into :class:`.Message` for example) and sent (answer to user's
message for example) by managers, actual :class:`.Message` or raw updates
from services is processed by :class:`.Executor`. They register callbacks
which receives updates (:class:`.Message` or raw updates from services).
Callbacks process updates one by one while callbacks returns anything but
`"DONE"`. If callback returns `"DONE"`, update is considered processed and is
dropped.

Callbacks has priorities. It's just a number, but in order to not get lost in
priorities it is highly recommended to use default priority - 400. It you
need to run your callback earlier, you can register your callback with
`early=True` argument. This will increase priority by 200, so it will be called
before most of usual callbacks.

Executers can use plugins. Plugins contains logically grouped callbacks with
orbitrary data like plugins's name, description etc. Plugins register their
callbacks in executor, and executer register callbacks in kutana. Plugins'
callbacks can return None (implicitly or explicitly) or `"DONE"` to mark
update as processed.

Callbacks
---------

Message processing
~~~~~~~~~~~~~~~~~~
Typical callback function (coroutine, actually) for message processing from
plugin looks like that:

.. code-block:: python

    @plugin.on_startswith_text("echo")
    async def on_echo_callback(message, env, body):
        await env.reply("{}".format(body))


Callback receives three arguments - :class:`.Message`, list of
:class:`.Attachment` and :class:`.Environment`. Environment
contains basic functions for interacting with data and user. It has methods
for replying, stores message that will be passed to next callback etc.

Raw updates processing
~~~~~~~~~~~~~~~~~~~~~~
Callback function for processing raw update from service looks like that:

.. code-block:: python

    @plugin.on_raw()
    async def on_raw_callback(update, env):
        pass


Callback receives two arguments - raw update's data as dict and
:class:`.Environment`. It's pretty straight forward and theese callbacks
is used when you need to add something special to workflow often connected with
concrete service.

Plugins
-------
See :class:`.Plugin` for list of available callback registators. Example
of simple plugin:

.. code-block:: python

    from kutana import Plugin

    plugin = Plugin(name="Echo")

    @plugin.on_startswith_text("echo")
    async def on_echo(message, env, body):
        await env.reply("{}".format(body))

Callback `on_echo` can have (or can not have) keyword arguments `body`,
`args`, `prefix`. Kutana will pass corresponding values to keywords. This
plugin can be registered in :class:`.Executor`.

.. note::

    Plugins uses callback's signature to determine if it needs to pass some
    arguments. It means that you have to use `functools.wraps` to properly
    wrap callback.

Exmaple of working engine with :class:`VKManager`:

.. code-block:: python

    from kutana import Kutana, VKManager, \
        load_plugins, load_configuration

    kutana = Kutana()

    manager = VKManager("API TOKEN")

    kutana.add_manager(manager)

    kutana.executor.register_plugins(
        load_plugins("plugins/")
    )

    kutana.run()

-------------------------------------------------------------------------------

.. toctree::
    :maxdepth: 1
    :caption: Managers

    VKManager <src/kutana.manager.vk>
    DebugManager <src/kutana.manager.debug>

.. toctree::
    :maxdepth: 1
    :caption: API Reference

    Plugin <src/kutana.plugin>
    src/modules
