from kutana import Plugin


plugin = Plugin(name="Statistics")


@plugin.on_startup()
async def on_startup(kutana, registered_plugins):
    plugin.stats = {}


@plugin.on_has_text(early=True)
async def on_any_message(message, env):
    words_count = plugin.stats.get(message.from_id, 0)

    new_words_count = words_count + len(message.text.split())

    plugin.stats[message.from_id] = new_words_count

    return "GOON"


@plugin.on_text("statistics")
async def on_show_statistics(message, env):
    await env.reply(
        "You wrote: {} words.".format(
            plugin.stats.get(message.from_id, 0)
        )
    )
