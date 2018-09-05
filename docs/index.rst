Welcome to Kutana!
==================================

.. image:: _static/kutana-logo-512.png
    :alt: Kutana

The engine for developing bots for soc. networks, 
instant messengers and other systems.

.. note::
    We apologize in advance for errors and omissions in this documentation. 
    If you can help improve the documentation corrections or modifications,
    we will be very grateful.

Usage
*****

- Create :class:`.Kutana` engine and add controllers. You can use 
  shortcuts like :class:`VKKutana <kutana.shortcuts.VKKutana>` for adding and registering controllers,
  callbacks and other usefull functions.
- You can set settings in `Kutana.settings`.
- Add or create plugins other files and register them in executor. You 
  can import plugin from files with function `load_plugins`. Files 
  should be a valid python modules with available `plugin` field with 
  your plugin (`Plugin`).
- Start engine.

Example
*******

Example "run.py"

.. code-block:: python

    from kutana import Kutana, VKKutana, load_plugins

    # Creation
    kutana = VKKutana(configuration="configuration.json")

    # Settings
    kutana.settings["MOTD_MESSAGE"] = "Greetings, traveler." 

    # Create simple plugin
    plugin = Plugin()

    @self.plugin.on_text("hi", "hi!")
    async def greet(message, attachments, env, extenv):
        await env.reply("Hello!")

    kutana.executor.register_plugins(plugin)

    # Load plugins from folder
    kutana.executor.register_plugins(*load_plugins("plugins/"))

    # Start kutana
    kutana.run()

Example "plugins/echo.py"

.. code-block:: python

    from kutana import Plugin

    plugin = Plugin()

    plugin.name = "Echo"

    @plugin.on_startswith_text("echo")
    async def on_message(message, attachments, env, extenv):
        await env.reply("{}!".format(env.body))

.. toctree::
    :maxdepth: 2
    :caption: Docs

    plugins
    controllers
    special-updates
    executors

.. toctree::
    :maxdepth: 1
    :caption: Source

    src/modules