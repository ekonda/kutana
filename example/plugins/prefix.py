from kutana import Plugin, Message


plugin = Plugin(name="Prefix", priority=5)  # default priority is 0


PREFIXES = (".", "/")


@plugin.on_has_text()
async def on_has_text(message, env):
    for prefix in PREFIXES:
        if message.text[:len(prefix)] == prefix:
            break

    else:
        return "DONE"

    env.parent.set_message(
        Message(
            message.text[len(prefix):],
            message.attachments,
            message.from_id,
            message.peer_id,
            message.date,
            message.raw_update
        )
    )

    return "GOON"
