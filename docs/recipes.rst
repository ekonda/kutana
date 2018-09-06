Recipes
=======

Check for prefix
^^^^^^^^^^^^^^^^

.. code-block:: python

    from kutana import Plugin, Message  # don't forget to import Message

    # this plugin should run before other plugins
    plugin = Plugin(name="Prefix", order=15)

    # you can import this value from your settings or something like that
    PREFIX = "/"

    @plugin.on_has_text()
    async def on_has_text(message, env, **kwargs):
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
