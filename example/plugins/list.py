from kutana import Plugin

plugin = Plugin(name="Plugins")

@plugin.on_startup()
async def on_startup(kutana, update):
    plugin.plugins = []

    for pl in update["callbacks_owners"]:
        if isinstance(pl, Plugin):
            plugin.plugins.append(pl.name)

@plugin.on_startswith_text("list")
async def on_list(message, attachments, env):
    await env.reply(
        "Plugins:\n" +
        " | ".join(plugin.plugins)
    )
