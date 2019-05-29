from kutana import Plugin

# Plugins for demonstrating how environment works

plugin1 = Plugin(name="Environment")


@plugin1.on_startswith_text("environment")
async def _(message, env):
    # Do or produce something and save it to **parent** environment.
    # Values saved to just "env" will be accesible only by other callback for
    # current plugin.
    env.parent.var = "val"

    # Let other plugins work
    return "GOON"


plugin2 = Plugin(name="_Environment_receiver")


@plugin2.on_startswith_text("environment")
async def _(message, env):
    await env.reply('env.var == "{}"'.format(
        env.var  # Use saved in environment by other plugin value
    ))


plugins = [plugin1, plugin2]  # Order matters
