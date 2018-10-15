from kutana import Plugin, get_path

plugin = Plugin(name="My file")

@plugin.on_startup()
async def on_startup(update, env):
    with open(get_path(__file__, "my_file")) as fh:
        plugin.my_file = fh.read().strip()
