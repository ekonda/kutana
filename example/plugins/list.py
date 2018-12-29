from kutana import Plugin


plugin = Plugin(name="Plugins")


@plugin.on_startup()
async def on_startup(kutana, registered_plugins):
    plugin.plugins = []

    for pl in registered_plugins:
        if isinstance(pl, Plugin) and hasattr(pl, "name"):
            plugin.plugins.append(pl.name)


@plugin.on_text("list")
async def on_list(message, env):
    await env.reply(
        "Plugins:\n" +
        " | ".join(plugin.plugins)
    )
