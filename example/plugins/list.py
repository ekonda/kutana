from kutana import Plugin


plugin = Plugin(name="Plugins")


plugins = []


@plugin.on_startup()
async def startup(app):
    plugins = []

    for pl in app.registered_plugins:
        if isinstance(pl, Plugin) and pl.name[:1] != "_":
            plugins.append(pl.name)


@plugin.on_text("list")
async def on_list(message, env):
    await env.reply(
        "Plugins:\n" + "; ".join(plugins)
    )
