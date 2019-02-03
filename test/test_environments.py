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

    def test_spawn(self):
        env = Environment("manager")
        inner_env = env.spawn()

        self.assertEqual(env.manager, inner_env.manager)
        self.assertEqual(env.parent, None)
        self.assertEqual(inner_env.parent, env)
