from kutana import Plugin

plugin = Plugin(
    name="Plugins",
    description="Lists installed plugins (.plugins)",
)


MESSAGE = ""


@plugin.on_start()
async def _():
    global MESSAGE

    MESSAGE = "Plugins:"

    for other in plugin.app.plugins:
        if not isinstance(other, Plugin):
            continue

        if hasattr(other, "name") and other.name.startswith("_"):
            continue

        MESSAGE += "\n- {} - {}".format(other.name, other.description)


@plugin.on_commands(["plugins"])
async def _(msg, ctx):
    await ctx.reply(MESSAGE)
