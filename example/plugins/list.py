from kutana import Plugin, load_plugins

plugin = Plugin()

plugin.name = "Plugins Lister"

@plugin.on_startup()
async def on_startup(kutana, update):
    plugin.plugins = []

    for pl in update["callbacks_owners"]:
        if isinstance(pl, Plugin):
            plugin.plugins.append(pl.name)

    plugin.bot_name = kutana.settings.get("bot_name", "noname")

@plugin.on_startswith_text("list")
async def on_message(message, attachments, env, extenv):
    await env.reply(
        "Bot with name \"{}\" has:\n".format(plugin.bot_name) +
        "; ".join(plugin.plugins)
    )