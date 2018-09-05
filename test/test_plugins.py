from test_framework import KutanaTest
import re


class TestPlugins(KutanaTest):
    def test_echo_plugin(self):
        queue = ["message", "echo message", "echonotecho"] * 10

        self.target = ["message"] * 10

        with self.dumping_controller(queue) as plugin:
            async def on_echo(message, env, **kwargs):
                self.actual.append(env.body)

            plugin.on_startswith_text("echo ", "echo\n")(on_echo)

    def test_plugin_on_raw(self):
        self.called = 0

        with self.dumping_controller("message") as plugin:
            async def on_startup(message, env, **kwargs):
                self.called += 1

            plugin.on_startup()(on_startup)

        self.assertEqual(self.called, 1)

    def test_plugin_callbacks(self):
        self.disposed = 0
        self.counter = 0

        with self.dumping_controller(["123"] * 10 + ["321"]) as plugin:
            async def on_123(message, **kwargs):
                self.assertEqual(message.text, "123")
                self.counter += 1

            plugin.on_text("123")(on_123)


            async def on_everything(message, **kwargs):
                self.assertNotEqual(message.text, "123")
                self.counter += 1

            plugin.on_has_text()(on_everything)


            async def on_raw(message, **kwargs):
                raise RuntimeError

            plugin.on_raw()(on_raw)


            async def on_dispose():
                self.disposed += 1

            plugin.on_dispose()(on_dispose)

        self.assertEqual(self.counter, 11)
        self.assertEqual(self.disposed, 1)

    def test_environment_reply(self):
        self.target = ["echo 123"] * 10 + ["ECHO 123"]

        with self.dumping_controller(self.target) as plugin:
            async def on_echo(message, env, **kwargs):
                self.assertEqual(env.reply, print)
                self.actual.append(message.text)

            plugin.on_startswith_text("echo")(on_echo)

    def test_plugin_onstar(self):
        queue = ["привет", "отлично привет", "ecHo", "ab", "ae", "hello"]
        self.result = 0

        with self.dumping_controller(queue) as plugin:
            async def no_trigger(message, **kwargs):
                self.assertTrue(False)

            plugin.on_attachment()(no_trigger)


            async def zero_trigger(message, **kwargs):
                self.result |= 1 << 0

            plugin.on_has_text("привет")(zero_trigger)


            async def one_trigger(message, **kwargs):
                self.result |= 1 << 1

            plugin.on_regexp_text(r"a(b|c)")(one_trigger)


            async def two_trigger(message, **kwargs):
                self.result |= 1 << 2

            plugin.on_regexp_text(re.compile(r"a(e|z)"))(two_trigger)


            async def three_trigger(message, **kwargs):
                self.result |= 1 << 3

            plugin.on_startswith_text("hell")(three_trigger)


            async def four_trigger(message, env, **kwargs):
                self.result |= 1 << 4

            plugin.on_text("ecHo")(four_trigger)

        self.assertEqual(self.result, (1 << 5) - 1)
