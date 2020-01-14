from kutana import Plugin, HandlerResponse


# Plugins for demonstrating how contexts works


plugin1 = Plugin(name="Contexts [Provider]")


@plugin1.on_commands(["contexts"], priority=5)
async def _(msg, ctx):
    # Do or produce something and save it to context.
    ctx.var = "val"

    # Let other plugins work
    return HandlerResponse.SKIPPED


plugin2 = Plugin(name="Contexts")


@plugin2.on_commands(["contexts"])
async def _(msg, ctx):
    await ctx.reply('ctx.var == "{}"'.format(
        ctx.var  # Use value saved in context by other plugin
    ))


plugins = [plugin1, plugin2]  # Order matters
