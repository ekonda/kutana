from kutana import Plugin, t


plugin = Plugin(name=t("Plugins"), description=t("Sends installed plugins (.plugins)"))


plugins = []


@plugin.on_start()
async def __(app):
    for pl in app.get_plugins():
        if isinstance(pl, Plugin) and not pl.name.startswith("$"):
            plugins.append(pl)


@plugin.on_commands(["plugins"])
async def __(msg, ctx):
    await ctx.reply(t("Plugins") + ":\n" + "\n".join(
        "- {} - {}".format(pl.name, pl.description) for pl in plugins
    ))
