import os
import time
import psutil
from kutana import Plugin, t


plugin = Plugin(name=t("Metrics"), description=t("Sends some information (.metrics)"))


@plugin.on_commands(["metrics"])
async def __(msg, ctx):
    process = psutil.Process(os.getpid())

    taken_memory = int(process.memory_info().rss / 2**20)
    taken_time = time.time() - msg.date

    await ctx.reply("mem: ~{}mib; tim: {}s".format(taken_memory, taken_time))
