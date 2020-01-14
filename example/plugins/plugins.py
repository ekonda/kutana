from kutana import Plugin


plugin = Plugin(name="Plugins", description="Show present plugins")


plugins = []


@plugin.on_start()
async def _(app):
    for pl in app.get_plugins():
        if isinstance(pl, Plugin) and pl.name[:1] != "_":
            plugins.append(pl.name)


@plugin.on_commands(["plugins"])
async def _(msg, ctx):
    lines = ("- {}".format(plugin) for plugin in plugins)

    await ctx.reply("Plugins:\n" + "\n".join(lines))
