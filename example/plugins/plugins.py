from kutana import Plugin


plugin = Plugin(name="Plugins", description="Show present plugins")


plugins = []


@plugin.on_startup()
async def _(app):
    for pl in app.registered_plugins:
        if isinstance(pl, Plugin) and pl.name[:1] != "_":
            plugins.append(pl.name)


@plugin.on_text("plugins")
async def _(message, env):
    lines = ("- {}".format(plugin) for plugin in plugins)

    await env.reply("Plugins:\n" + "\n".join(lines))
