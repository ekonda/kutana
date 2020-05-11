Kutana documentation
====================

.. image:: _static/kutana-logo-512.png
    :alt: Kutana
    :scale: 60%

.. note::
    We apologize in advance for errors and omissions in this documentation.
    If you can help improve the documentation correctness, we will be very
    grateful.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Overview
--------
Kutana is an engine for developing bots for social networks, messengers and
other services. Kutana heavily uses asyncio and coroutines. It supports
different backends (like vk.com, telegram.org etc.).

Refer to `example
<https://github.com/ekonda/kutana/tree/master/example/>`_ folder for
the showcase of the engine abilities.

Workflow
--------

In order to use kutana, you should initialize engine, add your backends
and plugins. After that you can run your application.

Below you can find the most simple `run.py` file for kutana application,
that uses one Vkontakte account and loads plugins from folder `plugins/`.

.. code-block:: python

    from kutana import Kutana, load_plugins
    from kutana.backends import Vkontakte

    app = Kutana()
    app.add_backend(Vkontakte(token=VK_API_TOKEN))
    app.add_plugins(load_plugins("plugins/"))
    app.run()

Plugins
-------

Main functionality for your applications are providee by plugins:
they can add commands, process and preprocess messages, e.t.c.

Below your can find example of simple plugin `echo.py` (that should
be put into `plugins` folder).

.. code-block:: python

    from kutana import Plugin

    plugin = Plugin(name="Echo", description="Reply with send message")

    @plugin.on_commands(["echo"])
    async def _(msg, ctx):
        await ctx.reply("{}".format(ctx.body), attachments=msg.attachments)

Handlers for messages receive :class:`kutana.update.Message` and
:class:`kutana.context.Context` as arguments. You can find description of
their methods for these classes in Full API.

You can find descriptions of all possible "on_*" methods for adding your
callbacks in :class:`kutana.plugin.Plugin` class.

Order of "on_*" methods
^^^^^^^^^^^^^^^^^^^^^^^
Default order of processors:

- on_messages, on_updates: 9
- on_payloads (vk): 7
- on_commands: 6
- on_attachments: 3
- on_unprocessed_messages, on_unprocessed_updates: -3
- Rest: ~0

Attachments
^^^^^^^^^^^

Interactions with backends are highly unified, because we want you to have
no problems creating plugins that will work nicely with multiple backends.

You can manage your attachments throught class :class:`kutana.update.Attachment`.
new attachments can be created using :meth:`kutana.update.Attachment.new`.

Attachments are files that can have types. If type is unique to backends -
you still can use them, but you will need to manager their uploads,
parsing, e.t.c. on your own.

Below you can find exmaple handler that will read and send three types
of attachments. Type "graffiti" is not present in vkontakte's backend,
so it can be seen as demonstartion of how to work with "custom" types.

.. code-block:: python

    @plugin.on_commands(["documents"])
    async def _(msg, ctx):
        path_to_pizza = get_path(__file__, "assets/pizza.png")
        path_to_audio = get_path(__file__, "assets/audio.ogg")

        # Document
        with open(path_to_pizza, "rb") as fh:
            doc = Attachment.new(
                fh.read(),
                "pizza.png"
            )

        await ctx.reply("Document", attachments=doc)

        # Graffiti (special for vk)
        with open(path_to_pizza, "rb") as fh:
            graffiti = Attachment.new(
                fh.read(),
                "pizza.png",
                type="graffiti"
            )

        await ctx.reply("Graffiti", attachments=graffiti)

        # Audio message
        with open(path_to_audio, "rb") as fh:
            audio_message = Attachment.new(
                fh.read(),
                "audio.ogg",
                "voice"
            )

        await ctx.reply("Audio message", attachments=audio_message)

Existing attachments (that already uploaded for example) can be created using
:meth:`kutana.update.Attachment.existing`. Many backends capable of forwarding
raw strings (supported by your service) while sending messages.

Available built-in attachment types:

- image
- doc
- sticker
- video
- audio
- voice

Not every backend can interact well with all the types, so you should
be careful. If you have troubling examples - create an issue in the
repository and we'll update documentation!

API Requests
^^^^^^^^^^^^

In order to perform a request to your service, your should use
:meth:`kutana.context.Context.request` method. It accepts method that you
want to use and any keyword arguments that should be processable by your
backend. You can check what backend context belongs to by accessing it's
`backend` attribute.

Storage
^^^^^^^

Kutana uses storage to store some information like user states. By default,
it uses :class:`kutana.storages.NaiveMemory` for storing data. If you need
to use more advanced storage, you can extend :class:`kutana.storage.Storage`
and implement it with any library and backend you want. Just pass storage to
the application constructor.

If you want load storage from the plugin, you still need to implement
your "Storage" and pass it to application. But you can delay initialization
until your database plugin's "on_start" method. You can access storage with
"app.storage".

But it's it's not recommended using the application's
storage as database for your plugins' data. Just implement methods and
access database in your plugin, if it's the case.


-------------------------------------------------------------------------------

.. toctree::
    :maxdepth: 1
    :caption: API Reference

    Backends <src/kutana.backends>
    Plugin <src/kutana.plugin>
    Kutana <src/kutana.kutana>
    Full API <src/modules>
