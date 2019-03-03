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
    If you can help improve the documentation correctness, we will be very
    grateful.

====================
Kutana documentation
====================

Overview
--------
Kutana is an engine for developing bots for social networks, messengers and
other services. Kutana heavily uses asyncio and coroutines. It supports
different backends (like vk.com, telegram.org etc.) through different
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

Callbacks has priorities. It's just a number, but to not get lost in
priorities it is highly recommended to use default priority - 0.

Executers can use plugins. Plugins contains logically grouped callbacks with
arbitrary data like plugins's name, description etc. Plugins register their
callbacks in executor, and executor register callbacks in kutana. Plugins'
callbacks can return None (implicitly or explicitly) or `"DONE"` to mark
update as processed.

Priority of plugins' callbacks works only in that plugin. If your want to
make plugin that does something before other plugins - you should split
your plugin into two parts: one with high priority, other with normal.

Environments
------------
Environments is objects with information and methods for interacting with
data and user. It has methods for replying, performing requests to API,
stores message that will be passed to next callback etc.

You can replace existing methods in environment with
:func:`kutana.environment.Environment.replace_method` and set your
fields to environment with dot notation `env.foo = "bar"`.

Every plugin works with copy of update's environment. That means, if you
want to pass anything to other plugins you need to use `env.parent.`
instead of just `env.`.

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


Callback receives three arguments - :class:`.Message` and
:class:`.Environment`.

Raw updates processing
~~~~~~~~~~~~~~~~~~~~~~
Callback function for processing only raw update from service looks like that:

.. code-block:: python

    @plugin.on_raw()
    async def on_raw_callback(update, env):
        pass


Callback receives two arguments - raw update's data as dict and
:class:`.Environment`. It's pretty straight forward and these callbacks
is used when you need to add something special to workflow often
connected with concrete service.

Plugins
-------
See :class:`.Plugin` for list of available callback registrators. Example
of simple plugin:

.. code-block:: python

    from kutana import Plugin

    plugin = Plugin(name="Echo")

    @plugin.on_startswith_text("echo")
    async def on_echo(message, env, body):
        await env.reply("{}".format(body))

Callback `on_echo` can have (or not have) keyword arguments `body`,
`args`, `prefix`. Kutana will pass corresponding values to keywords. You
should use :func:`functools.wraps` decorator to save signatures of your
coroutines to allow kutana to find keyword arguments in decorated callbacks.
This plugin can be registered in :class:`.Executor`.

.. note::

    Plugins use callback's signature to decide if it needs to pass some
    arguments. It means that you have to use :func:`functools.wraps` to
    properly wrap callback.

Example of working engine with :class:`.VKManager`:

.. code-block:: python

    from kutana import Kutana, VKManager, \
        load_plugins, load_value

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
    TGManager <src/kutana.manager.tg>
    DebugManager <src/kutana.manager.debug>

.. toctree::
    :maxdepth: 1
    :caption: API Reference

    Plugin <src/kutana.plugin>
    src/modules
