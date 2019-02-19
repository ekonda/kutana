import asyncio

from kutana import Environment

from test_framework import KutanaTest


class TestEnvironments(KutanaTest):
    def test_replace_method(self):
        messages = []

        async def save(self, message):
            messages.append(message)

        env = Environment(None)
        env.replace_method("reply", save)

        asyncio.get_event_loop().run_until_complete(
            env.reply("message")
        )

        self.assertEqual(messages, ["message"])

    def test_replace_method_child_environments(self):
        env = Environment(None)

        def method_1(self, message):
            return 1

        def method_2(self, file):
            return 2

        env.replace_method("reply", method_1)
        env.replace_method("upload_doc", method_2)

        self.assertEqual(env.reply("_"), 1)
        self.assertEqual(env.upload_doc(b"_"), 2)

        child_env = env.spawn()

        self.assertEqual(child_env.reply("_"), 1)
        self.assertEqual(child_env.upload_doc(b"_"), 2)

        child_child_env = child_env.spawn()

        self.assertEqual(child_child_env.reply("_"), 1)
        self.assertEqual(child_child_env.upload_doc(b"_"), 2)

    def test_spawn(self):
        env = Environment("manager")
        inner_env = env.spawn()

        self.assertEqual(env.manager, inner_env.manager)
        self.assertEqual(env.parent, None)
        self.assertEqual(inner_env.parent, env)
