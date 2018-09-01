if __name__ == '__main__':
    import sys, os
    sys.path.append(os.getcwd())


from kutana import DumpingController, Plugin
from test_framework import KutanaTest
import unittest
import time


class TestTiming(KutanaTest):
    def test_exec_time(self):
        self.target = [";)", "echo message"] * 1000

        stime = time.time()

        with self.dumping_controller(self.target) as plugin:
            async def on_echo(message, env, **kwargs):
                self.actual.append("echo " + env.body)

            plugin.on_startswith_text("echo ", "echo\n")(on_echo)


            async def on_regexp(message, env, **kwargs):
                self.actual.append(env.match.group(0))

            plugin.on_regexp_text(r";\)")(on_regexp)


            stime = time.time()

        print("\nTIME TEST 1: ~{} ( {} )".format(
            (time.time() - stime) / 2000,
            time.time() - stime
        ))

        self.assertLess(time.time() - stime, 0.5)

    def test_raw_exec_time(self):
        self.target = ["message"] * 10000

        with self.dumping_controller(self.target) as plugin:
            async def on_any(message, env, **kwargs):
                self.actual.append("message")

            plugin.on_has_text()(on_any)


            stime = time.time()

        print("\nTIME TEST 2: ~{} ( {} )".format(
            (time.time() - stime) / 10000,
            time.time() - stime
        ))

        self.assertLess(time.time() - stime, 2)


if __name__ == '__main__':
    unittest.main()
