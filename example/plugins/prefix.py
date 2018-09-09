from kutana import Plugin, Message

plugin = Plugin(name="Prefix", priority=75)

PREFIX = "/"

@plugin.on_has_text()
async def on_has_text(message, env, **kwargs):
    if not message.text.startswith(PREFIX):
        return "DONE"

    env.eenv._cached_message = Message(
        message.text[len(PREFIX):],
        message.attachments,
        message.from_id,
        message.peer_id,
        message.raw_update
    )

    return "GOON"
