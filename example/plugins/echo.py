from kutana import Plugin

plugin = Plugin(name="Echo", description="Sends your messages back (.echo)")


@plugin.on_commands(["echo"])
async def _(message, context):
    await context.reply(
        "{}".format(context.body or "(/)"), attachments=message.attachments
    )
