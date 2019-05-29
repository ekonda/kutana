from kutana import Plugin


# Plugin's global variable
statistics = {}


# Sub-plugin to collect statistics
p1 = Plugin(name="_Statistics collector", priority=10)


@p1.on_has_text()
async def _(message, env):
    words_count = statistics.get(message.from_id, 0)

    new_words_count = words_count + len(message.text.split())

    statistics[message.from_id] = new_words_count

    return "GOON"


# Sub-plugin to show statistics
p2 = Plugin(name="Statistics", description="Show word count in current dialog")


@p2.on_text("statistics")
async def _(message, env):
    await env.reply(
        "You wrote: {} words.".format(statistics.get(message.from_id, 0))
    )


# List of plugins to export
plugins = [p1, p2]
