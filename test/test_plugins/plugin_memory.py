from kutana import Plugin

plugin = Plugin(name="Memory")

@plugin.on_has_text()
async def on_text(message, **kwargs):
    plugin.memory = message.text
