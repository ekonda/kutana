from kutana import Plugin, HandlerResponse


# Plugin's global variable
statistics = {}


# Sub-plugin to collect statistics
plugin = Plugin(
    name="Statistics",
    description="Show word count in current dialog",
)


@plugin.on_any_message(priority=5)
async def _(msg, ctx):
    words_count = statistics.get(msg.sender_id, 0)

    new_words_count = words_count + len(msg.text.split())

    statistics[msg.sender_id] = new_words_count

    return HandlerResponse.SKIPPED


@plugin.on_commands(["statistics"])
async def _(msg, ctx):
    await ctx.reply(
        "You wrote: {} words.".format(statistics.get(msg.sender_id, 0))
    )
