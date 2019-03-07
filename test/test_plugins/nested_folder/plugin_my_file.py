from kutana import Plugin, get_path

pl1 = Plugin(name="My file")

@pl1.on_startup()
async def startup_1(app):
    with open(get_path(__file__, "my_file")) as fh:
        pl1.my_file = fh.read().strip()

pl2 = Plugin(name="My file twice")

@pl2.on_startup()
async def startup_2(app):
    with open(get_path(__file__, "my_file")) as fh:
        pl2.my_file = fh.read().strip() * 2

plugins = [pl1, pl2]
