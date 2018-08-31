from kutana import Kutana, DumpingController, Plugin
from contextlib import contextmanager
from test_framework import KutanaTest
import unittest


class TestPlugins(KutanaTest):
    def test_echo_plugin(self):
        queue = ["message", "echo message", "echonotecho"] * 10
        
        self.target = ["message"] * 10 

        with self.dumping_controller(queue) as plugin:
            @plugin.on_startswith_text("echo ", "echo\n")
            async def on_echo(message, env, **kwargs):
                self.actual.append(env.body)

    def test_plugin_callbacks(self):
        self.disposed = 0
        self.counter = 0

        with self.dumping_controller(["123"] * 10 + ["321"]) as plugin:
            @plugin.on_text("123")
            async def on_123(message, **kwargs):
                self.assertEqual(message.text, "123")
                self.counter += 1

            @plugin.on_has_text()
            async def on_everything(message, **kwargs):
                self.assertNotEqual(message.text, "123")
                self.counter += 1

            @plugin.on_raw()
            async def on_raw(message, **kwargs):
                raise RuntimeError

            @plugin.on_dispose()
            async def on_dispose():
                self.disposed += 1

        self.assertEqual(self.counter, 11)
        self.assertEqual(self.disposed, 1)

    def test_environment_reply(self):
        self.target = ["echo 123"] * 10 + ["ECHO 123"]

        with self.dumping_controller(self.target) as plugin:
            @plugin.on_startswith_text("echo")
            async def on_123(message, env, **kwargs):
                self.assertEqual(env.reply, print)
                self.actual.append(message.text)

    def test_plugin_onstar(self):
        queue = ["привет", "отлично привет", "ecHo", "ab", "hello"]
        self.result = 0

        with self.dumping_controller(queue) as plugin:
            @plugin.on_attachment()
            async def no_trigger(message, **kwargs):
                self.assertTrue(False)

            @plugin.on_has_text("привет")
            async def zero_trigger(message, **kwargs):
                self.result |= 1 << 0

            @plugin.on_regexp_text(r"a(b|c)")
            async def one_trigger(message, **kwargs):
                self.result |= 1 << 1

            @plugin.on_startswith_text("hell")
            async def two_trigger(message, **kwargs):
                self.result |= 1 << 2

            @plugin.on_text("ecHo")
            async def three_trigger(message, env, **kwargs):
                self.result |= 1 << 3

        self.assertEqual(self.result, (1 << 4) - 1)
            
