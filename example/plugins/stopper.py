from kutana import Plugin


plugin = Plugin(name="Stop", description="Turns application off")


@plugin.on_start()
async def __(app):
    plugin.stop = app.stop


@plugin.on_commands(["stop"])
async def __(msg, ctx):
    plugin.stop()
