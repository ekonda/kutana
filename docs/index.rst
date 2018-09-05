Welcome to Kutana!
==================

.. image:: _static/kutana-logo-512.png
    :alt: Kutana
    :scale: 65%

The engine for developing bots for soc. networks,
instant messengers and other systems.

.. note::
    We apologize in advance for errors and omissions in this documentation.
    If you can help improve the documentation corrections or modifications,
    we will be very grateful.

Usage
*****

- Create :class:`.Kutana` engine and add controllers.
- Register your plugins in the executor. You can import
  plugin from folders with function `load_plugins`. Files
  should be a valid python modules with available `plugin`
  field with your plugin (`Plugin`).
- Start engine.

Example
*******

Example "run.py"

.. code-block:: python

    from kutana import Kutana, VKController, \
        load_plugins, load_configuration

    # Create engine
    kutana = Kutana()

    # Add VKController to engine
    kutana.add_controller(
        VKController(
            load_configuration(
                "vk_token", "configuration.json"
            )
        )
    )

    # Load and register plugins
    kutana.executor.register_plugins(
        *load_plugins("plugins/")
    )

    # Run engine
    kutana.run()


Example "plugins/echo.py"

.. code-block:: python

    from kutana import Plugin

    plugin = Plugin(name="Echo")

    @plugin.on_startswith_text("echo")
    async def on_echo(message, attachments, env):
        await env.reply("{}".format(env.body))

.. toctree::
    :maxdepth: 2
    :caption: Elements

    plugin
    controller
    special-updates
    executor

.. toctree::
    :maxdepth: 1
    :caption: Reference

    src/modules
