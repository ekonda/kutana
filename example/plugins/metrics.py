import os
import time

import psutil

from kutana import Plugin

plugin = Plugin(name="Metrics", description="Sends some information (.metrics)")


@plugin.on_commands(["metrics"])
async def _(msg, ctx):
    process = psutil.Process(os.getpid())

    taken_memory = int(process.memory_info().rss / 2**20)
    taken_time = time.time() - msg.date

    await ctx.reply("memory: ~{}mib; time: {}s".format(taken_memory, taken_time))
