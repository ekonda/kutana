from kutana import Plugin
from test_framework import KutanaTest
import re


class TestPlugins(KutanaTest):
    def test_plugin_creation(self):
        plugin = Plugin(name="Name", cmds=["cmd1", "cmd2"])

        self.assertEqual(plugin.name, "Name")  # pylint: disable=E1101
        self.assertEqual(plugin.cmds, ["cmd1", "cmd2"])  # pylint: disable=E1101

        plugin = Plugin(order=5)

    def test_echo_plugin(self):
        queue = ["message", "echo message", "echonotecho"] * 5

        self.target = ["message"] * 5

        with self.dumping_controller(queue) as plugin:
            async def on_echo(message, env, **kwargs):
                self.actual.append(env.body)

            plugin.on_startswith_text("echo ", "echo\n")(on_echo)

    def test_plugin_on_startup(self):
        self.called = 0

        with self.dumping_controller("message") as plugin:
            async def on_startup(message, env, **kwargs):
                self.called += 1

            plugin.on_startup()(on_startup)

        self.assertEqual(self.called, 1)

    def test_args_on_startswith_text(self):
        queue = ["pr a b c", "pr a \"b c\"", "pr a \"\\\"\" b c"]

        queue_answer = [
            ["a", "b", "c"], ["a", "b c"], ["a", "\"", "b", "c"]
        ]

        with self.dumping_controller(queue) as plugin:
            async def on_startswith_text(message, env, **kwargs):
                self.assertEqual(env.args, queue_answer.pop(0))

            plugin.on_startswith_text("pr")(on_startswith_text)

        self.assertFalse(queue_answer)

    def test_plugins_callbacks_done(self):
        self.counter = 0

        with self.dumping_controller(["123"] * 5) as plugin:

            async def on_has_text(message, **kwargs):
                self.counter += 1

                return "DONE"

            plugin.on_has_text("123")(on_has_text)

            async def on_has_text_2(message, **kwargs):
                self.counter += 1

            plugin.on_has_text("123")(on_has_text_2)

        self.assertEqual(self.counter, 5)

    def test_plugins_callbacks_not_done(self):
        self.counter = 0

        with self.dumping_controller(["123"] * 5) as plugin:

            async def on_has_text(message, **kwargs):
                self.counter += 1

                return "GOON"

            plugin.on_has_text("123")(on_has_text)

            async def on_has_text_2(message, **kwargs):
                self.counter += 1

            plugin.on_has_text("123")(on_has_text_2)

        self.assertEqual(self.counter, 10)

    def test_multiple_plugins(self):
        self.counter = 0

        with self.dumping_controller(["msg"] * 2):
            self.plugins.append(Plugin())
            self.plugins.append(Plugin())

            async def on_has_text(message, env, **kwargs):
                self.counter += 1

                self.assertNotIn("key", env)
                env["key"] = "value"

                return "GOON"

            for pl in self.plugins:
                pl.on_has_text()(on_has_text)

        self.assertEqual(self.counter, 6)

    def test_plugin_callbacks(self):
        self.disposed = 0
        self.counter = 0

        with self.dumping_controller(["123"] * 5 + ["321"]) as plugin:
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

        self.assertEqual(self.counter, 6)
        self.assertEqual(self.disposed, 1)

    def test_environment_reply(self):
        self.target = ["echo 123"]

        with self.dumping_controller(self.target) as plugin:
            async def on_echo(message, env, **kwargs):
                self.assertIsNotNone(env.reply)
                self.actual.append(message.text)

            plugin.on_startswith_text("echo")(on_echo)

    def test_plugin_onstar(self):
        queue = ["привет", "отлично привет", "ecHo", "ab", "ae", "hello"]
        self.result = 0

        with self.dumping_controller(queue) as plugin:
            async def no_trigger(message, **kwargs):
                self.assertTrue(False)

            plugin.on_attachment("photo", "audio")(no_trigger)


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
