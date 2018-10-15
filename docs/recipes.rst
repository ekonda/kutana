Recipes
=======

Check for prefix
^^^^^^^^^^^^^^^^

.. code-block:: python

    from kutana import Plugin, Message  # don't forget to import Message

    # this plugin should run before other plugins
    plugin = Plugin(name="Prefix", priority=500)

    # Priority:
    # 400 is normal plugins (usually)
    # 600 is early callbacks (400 + 200)
    # 500 is between
    #
    # That means early plugins works without prefix!


    # you can import this value from your settings or something like that
    PREFIX = "/"

    @plugin.on_has_text()
    async def on_has_text(message, attachments, env):
        if not message.text.startswith(PREFIX):
            return "DONE"  # "GOON" if you want to just keep message

        # replace message with your own with removed prefix for other plugins
        env.eenv._cached_message = Message(
            message.text[len(PREFIX):],
            message.attachments,
            message.from_id,
            message.peer_id,
            message.raw_update
        )

        # tell executor to keep processing current update
        return "GOON"

Use controller on startup
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    @plugin.on_startup()
    async def on_startup(update, env):
        controller = update["kutana"].controllers[-1]

        # create environment for your execution
        fake_env = objdict()

        # setup environment with fake update
        await controller.setup_env(
            {"object": {}, "type": "fake"},
            fake_env
        )

        # !!! Note that on startup update no control
        # !!! looops are runnning.
        # !!! That means just calling and awaiting from
        # !!! coroutines like send_message will NOT work.
        #
        # !!! You sould use update["kutana"].ensure_future

        update["kutana"].ensure_future(
            fake_env.send_message(
                "Hello world!",
                peer_id=87641997
            )
        )

        # etc.

Initiate with controller
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from kutana import Kutana, VKController, load_plugins, \
        load_configuration

    # Create engine
    kutana = Kutana()

    # Create VKController
    controller = VKController(
        load_configuration("vk_token", "configuration.json")
    )

    # Do your things
    async def my_init():
        async with controller:
            await controller.raw_request("users.get")

        # also possible
        async with VKController(token="token") as ctrl:
            await ctrl.raw_request("users.get")

    # It's important to use "raw_request" and not "request".
    # Method "request" is not working outside of running engine.

    kutana.loop.run_until_complete(my_init())

    # Add controller to engine
    kutana.add_controller(controller)

    # Load and register plugins
    kutana.executor.register_plugins(
        *load_plugins("example/plugins/")
    )

    # Run engine
    kutana.run()

    # You can also do your things here after bot stopped.
