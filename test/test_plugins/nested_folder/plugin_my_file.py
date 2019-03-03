from kutana import Plugin, get_path

pl1 = Plugin(name="My file")

@pl1.on_startup()
async def on_startup_1(kutana, registered_plugins):
    with open(get_path(__file__, "my_file")) as fh:
        pl1.my_file = fh.read().strip()

pl2 = Plugin(name="My file twice")

@pl2.on_startup()
async def on_startup_2(kutana, registered_plugins):
    with open(get_path(__file__, "my_file")) as fh:
        pl2.my_file = fh.read().strip() * 2

plugins = [pl1, pl2]
