from kutana import Plugin, Message


plugin = Plugin(name="Prefix", priority=500)


# Priority:
# 400 is normal plugins (usually)
# 600 is early normal callbacks (400 + 200)
# 500 is between
#
# That means early plugins works without prefix!
#
# If you need better prefix system, check github.com/ekonda/kubot


PREFIX = (".", "/")


@plugin.on_has_text()
async def on_has_text(message, env):
    for prefix in PREFIX:
        if message.text[:len(prefix)] == prefix:
            break

    else:
        return "DONE"

    env.parent_environment.set_message(
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
