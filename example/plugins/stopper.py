from kutana import Plugin


plugin = Plugin(name="Stop", description="Turns application off")


@plugin.on_start()
async def _(app):
    plugin.stop = app.stop


@plugin.on_commands(["stop"])
async def _(msg, ctx):
    plugin.stop()
