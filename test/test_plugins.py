import asyncio
import re

from kutana import Attachment, DebugEnvironment, Message, Plugin

from testing_tools import KutanaTest


class TestPlugins(KutanaTest):
    def test_plugin_creation(self):
        plugin = Plugin(name="Name", cmds=["cmd1", "cmd2"])

        self.assertEqual(plugin.name, "Name")  # pylint: disable=E1101
        self.assertEqual(plugin.cmds, ["cmd1", "cmd2"])  # pylint: disable=E1101

        plugin = Plugin(priority=1000)

    def test_echo_plugin(self):
        queue = ["message", "echo message", "echonotecho"]

        self.target = ["message"]

        with self.debug_manager(queue) as plugin:

            @plugin.on_startswith_text("echo ", "echo\n")
            async def _(message, env):
                await env.reply(env.body)

    def test_plugin_on_startup(self):
        self.called = 0

        with self.debug_manager(["message"]) as plugin:

            @plugin.on_startup()
            async def startup(app):
                self.called += 1

        self.assertEqual(self.called, 1)

    def test_plugin_register(self):
        self.answers = []

        with self.debug_manager(["message"]) as plugin:

            async def cb_1(update, env):
                self.answers.append(1)

            async def cb_2(update, env):
                self.answers.append(2)

            async def cb_3(update, env):
                self.answers.append(3)

            plugin.register(cb_1)
            plugin.register(cb_2, priority=1)
            plugin.register(cb_3)

        self.assertEqual(self.answers, [2, 1, 3])

    def test_plugin_register_two_plugins(self):
        self.answers = []

        with self.debug_manager(["message"]) as plugin1:

            plugin2 = Plugin(priority=1)

            self.plugins.append(plugin2)

            async def cb_1(update, env):
                self.answers.append(1)

            async def cb_2(update, env):
                self.answers.append(2)

            async def cb_3(update, env):
                self.answers.append(3)

            plugin1.register(cb_1)
            plugin2.register(cb_3)
            plugin1.register(cb_2, priority=1)

        self.assertEqual(self.answers, [3, 2, 1])

    def test_args_on_startswith_text(self):
        queue = ["pr a b c", "pr a \"b c\"", "pr ab c"]

        queue_answer = [
            ["a", "b", "c"], ["a", "\"b", "c\""], ["ab", "c"]
        ]

        with self.debug_manager(queue) as plugin:

            @plugin.on_startswith_text("pr")
            async def _(message, env):
                self.assertEqual(env.args, queue_answer.pop(0))

        self.assertFalse(queue_answer)

    def test_environments(self):
        self.target = ["1", "2"]

        with self.debug_manager(["123", ".hi arg1 arg2"]) as plugin:

            @plugin.on_has_text("12")
            async def _(msg, env):
                self.assertEqual(env.found_text, "12")
                await env.reply("1")

            @plugin.on_startswith_text(".")
            async def _(msg, env):
                self.assertEqual(env.args, ["hi", "arg1", "arg2"])
                self.assertEqual(env.body, "hi arg1 arg2")
                self.assertEqual(env.prefix, ".")
                await env.reply("2")

    def test_plugins_callbacks_done(self):
        self.counter = 0

        with self.debug_manager(["123"]) as plugin:

            @plugin.on_has_text("123")
            async def _(message, env):
                self.counter += 1
                return "DONE"

            @plugin.on_has_text("123")
            async def _(message, env):
                self.counter += 1

        self.assertEqual(self.counter, 1)

    def test_plugins_callbacks_not_done(self):
        self.counter = 0

        with self.debug_manager(["123"]) as plugin:

            @plugin.on_has_text("123")
            async def _(message, env):
                self.counter += 1
                return "GOON"

            @plugin.on_has_text("123")
            async def _(message, env):
                self.counter += 1

        self.assertEqual(self.counter, 2)

    def test_multiple_plugins(self):
        self.counter = 0

        with self.debug_manager(["message"]):

            self.plugins.append(Plugin())
            self.plugins.append(Plugin())

            for pl in self.plugins:
                @pl.on_has_text()
                async def _(message, env):
                    self.counter += 1
                    return "GOON"

        self.assertEqual(self.counter, 3)

    def test_early_callbacks(self):
        self.answers = []

        with self.debug_manager(["message"]):

            @self.plugin.on_has_text(priority=1)
            async def _(message, env):
                self.answers.append("early")

                return "GOON"

            @self.plugin.on_has_text()
            async def _(message, env):
                self.answers.append("late")

        self.assertEqual(self.answers, ["early", "late"])

    def test_early_callbacks_raw(self):
        self.answers = []

        with self.debug_manager([None]):

            @self.plugin.on_raw(priority=1)
            async def _(update, env):
                self.answers.append("early")

                return "GOON"

            @self.plugin.on_raw()
            async def _(update, env):
                self.answers.append("late")

        self.assertEqual(self.answers, ["early", "late"])

    def test_plugin_callbacks(self):
        self.disposed = 0
        self.counter = 0

        with self.debug_manager(["123", "321"]) as plugin:

            @plugin.on_text("123")
            async def _(message, env):
                self.assertEqual(message.text, "123")
                self.counter += 1

            @plugin.on_has_text()
            async def _(message, env):
                self.assertNotEqual(message.text, "123")
                self.counter += 1

            @plugin.on_raw()
            async def _(update, env):
                raise RuntimeError

            @plugin.on_dispose()
            async def _():
                self.disposed += 1

        self.assertEqual(self.counter, 2)
        self.assertEqual(self.disposed, 1)

    def test_reply(self):
        self.target = ["echo message"]

        with self.debug_manager(self.target) as plugin:

            @plugin.on_startswith_text("echo")
            async def _(message, env):
                await env.reply(message.text)

    def test_plugin_no_attachments_type(self):
        plugin = Plugin()

        @plugin.on_attachment("photo")
        async def _(message, env):
            return "DONE"

        wrapper = plugin._callbacks[0][1]

        attachments = [
            Attachment("audio", 0, 0, 0, 0, {}),
            Attachment("video", 0, 0, 0, 0, {})
        ]

        res = asyncio.get_event_loop().run_until_complete(
            wrapper(
                Message("", attachments, 0, 0, 0, {}),
                DebugEnvironment(None, 0)
            )
        )

        self.assertEqual(res, None)

    def test_plugin_attachments(self):
        plugin = Plugin()

        async def on_attachment(message, env):
            return "DONE"

        plugin.on_attachment()(on_attachment)

        wrapper = plugin._callbacks[0][1]

        res = asyncio.get_event_loop().run_until_complete(
            wrapper(
                Message("text", ("attachment"), 0, 0, 0, {}),
                DebugEnvironment(None, 0)
            )
        )

        self.assertEqual(res, "DONE")

    def test_plugin_attachments_type(self):
        plugin = Plugin()

        @plugin.on_attachment("photo")
        async def _(message, env):
            return "DONE"

        wrapper = plugin._callbacks[0][1]

        res = asyncio.get_event_loop().run_until_complete(
            wrapper(
                Message(
                    "text", [Attachment("photo", 0, 0, 0, 0, {})], 0, 0, 0, {}
                ),
                DebugEnvironment(None, 0)
            )
        )

        self.assertEqual(res, "DONE")

    def test_plugin_no_text(self):
        plugin = Plugin()

        @plugin.on_has_text()
        async def _(message, env):
            return "DONE"

        wrapper = plugin._callbacks[0][1]

        res = asyncio.get_event_loop().run_until_complete(
            wrapper(
                Message("", ("attachment"), 0, 0, 0, {}),
                DebugEnvironment(None, 0)
            )
        )

        self.assertNotEqual(res, "DONE")

    def test_on_message(self):
        plugin = Plugin()

        @plugin.on_message()
        async def _(message, env):
            return "DONE"

        wrapper = plugin._callbacks[0][1]

        res = asyncio.get_event_loop().run_until_complete(
            wrapper(
                Message("", ("attachment"), 0, 0, 0, {}),
                DebugEnvironment(None, 0)
            )
        )

        self.assertEqual(res, "DONE")

    def test_plugin_onstar(self):
        queue = ["привет", "отлично привет", "ecHo", "ab", "ae", "hello"]
        self.result = 0

        with self.debug_manager(queue) as plugin:

            @plugin.on_attachment("photo", "audio")
            async def _(message, env):
                self.assertTrue(False)

            @plugin.on_has_text("привет")
            async def _(message, env):
                self.result |= 1 << 0

            @plugin.on_regexp_text(r"a(b|c)")
            async def _(message, env):
                self.assertTrue(env.match.group(0), "ab")
                self.result |= 1 << 1

            @plugin.on_regexp_text(re.compile(r"a(e|z)"))
            async def _(message, env):
                self.result |= 1 << 2

            @plugin.on_startswith_text("hell")
            async def _(message, env):
                self.result |= 1 << 3

            @plugin.on_text("ecHo")
            async def _(message, env):
                self.result |= 1 << 4

        self.assertEqual(self.result, (1 << 5) - 1)
