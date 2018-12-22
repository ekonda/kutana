from kutana import Plugin
import psutil
import time
import os

plugin = Plugin(name="Metrics")

@plugin.on_startswith_text("metrics")
async def on_metrics(message, env):
    process = psutil.Process(os.getpid())

    taken_memory = int(process.memory_info().rss / 2**20)
    taken_time = time.time() - message.raw_update["object"]["date"]

    await env.reply("mem: ~{}mib; tim: {}".format(taken_memory, taken_time))
