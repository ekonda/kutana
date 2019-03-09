if __name__ == '__main__':
    import sys
    import os


    sys.path.insert(0, os.getcwd())


import time
import unittest

from testing_tools import KutanaTest


class TestTiming(KutanaTest):
    def test_exec_time(self):
        self.target = ["message", "echo message"] * 5000

        stime = time.time()

        with self.debug_manager(self.target) as plugin:

            async def on_echo(message, env):
                await env.reply("echo " + env.body)

            plugin.on_startswith_text("echo ", "echo\n")(on_echo)


            async def on_regexp(message, env):
                await env.reply(env.match.group(0))

            plugin.on_regexp_text(r"message")(on_regexp)

            stime = time.time()

        print("\nTIME TEST 1: ~{} ( {} )".format(
            (time.time() - stime) / 10000,
            time.time() - stime
        ))

        self.assertLess(time.time() - stime, 1)

    def test_raw_exec_time(self):
        self.target = ["message"] * 10000

        with self.debug_manager(self.target) as plugin:

            async def on_any(message, env):
                await env.reply("message")

            plugin.on_has_text()(on_any)

            stime = time.time()

        print("\nTIME TEST 2: ~{} ( {} )".format(
            (time.time() - stime) / 10000,
            time.time() - stime
        ))

        self.assertLess(time.time() - stime, 1)


if __name__ == '__main__':
    unittest.main()
