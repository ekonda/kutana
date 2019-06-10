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

Refer to `example
<https://github.com/ekonda/kutana/tree/master/example/>`_ for
the showcase of the engine abilities.

Workflow
--------
Managers are responsible for receiving and sending data. While data is prepared
(turned into :class:`.Message` for example) and sent (answer to user's
message for example) by managers, actual :class:`.Message` or raw updates
from services is processed callbacks. They registered in :class:`.Kutana`.
These callbacks receive updates (:class:`.Message` or raw updates
from services).

Callbacks process updates one by one while callbacks return anything but
`"DONE"`. If callback returns `"DONE"`, the update is considered processed
and is dropped.

Callbacks have priorities. It's just a number, but to not get lost in
priorities it is highly recommended to use default priority - 0.

The application can contain Plugins. Plugins contain logically grouped
callbacks with arbitrary data like plugin's name, description, etc.
Plugins register their callbacks in the executor, and executor register
callbacks in kutana. Plugins' callbacks can return None (implicitly or
explicitly) or `"DONE"` to mark an update as processed.

The priority of plugins' callbacks works only in that plugin. If you want to
make a plugin that does something before (or after) other plugins - you
should split your plugin into two parts: one with high priority, other
with normal (0).

`kutana.load_plugins` recursively check all python modules files from
the specified directory. When it finds a global variable `plugin`, it will be
added to the loaded plugins' list. When it finds a global variable `plugins`,
every plugin inside of it will be added to the loaded plugins' list.

Environments
------------
Environments are objects with information and methods for interacting with
data and user. It has methods for replying, performing requests to API,
stores message that will be passed to next callback e.t.c.

You can replace existing methods in environment with
:func:`kutana.environment.Environment.replace_method` and set your
fields to environment with dot notation `env.foo = "bar"`.

Every plugin works with a copy of the update's environment. That means if you
want to pass anything to other plugins you need to use `env.parent.`
instead of just `env.`.

Callbacks
---------

Message processing
~~~~~~~~~~~~~~~~~~
The typical callback coroutine for message processing from the plugin
looks like that:

.. code-block:: python

    @plugin.on_startswith_text("echo")
    async def on_echo_callback(message, env):
        await env.reply("{}".format(env.body))


THe callback receives two arguments - :class:`.Message` and
:class:`.Environment`.

Raw updates processing
~~~~~~~~~~~~~~~~~~~~~~
The callback function for processing only raw update from service
looks like that:

.. code-block:: python

    @plugin.on_raw()
    async def on_raw_callback(update, env):
        pass


The callback receives two arguments - raw update's data as dict and
:class:`.Environment`. It's pretty straight forward and these callbacks
are used when you need to add something special to workflow often
connected with concrete service.

Plugins
-------
See :class:`.Plugin` for list of available callback registrators. Example
of the simple plugin:

.. code-block:: python

    from kutana import Plugin

    plugin = Plugin(name="Echo")

    @plugin.on_startswith_text("echo")
    async def on_echo(message, env):
        await env.reply("{}".format(env.body))

Example of working engine with :class:`.VKManager`:

.. code-block:: python

    from kutana import Kutana, VKManager, load_plugins

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
    :caption: Managers and environments

    VKontakte <src/kutana.manager.vk>
    Telegram <src/kutana.manager.tg>

.. toctree::
    :maxdepth: 1
    :caption: API Reference

    Plugin <src/kutana.plugin>
    Kutana <src/kutana.kutana>
    Full API <src/modules>
