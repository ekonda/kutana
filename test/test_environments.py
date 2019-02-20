import asyncio

from kutana import Environment, VKEnvironment, TGEnvironment

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

        def method_3(self, message):
            return 3

        env.replace_method("reply", method_1)
        env.replace_method("upload_doc", method_2)

        self.assertEqual(env.reply("_"), 1)
        self.assertEqual(env.upload_doc(b"_"), 2)

        child_env = env.spawn()

        child_env.replace_method("reply", method_3)

        self.assertEqual(child_env.reply("_"), 3)
        self.assertEqual(child_env.upload_doc(b"_"), 2)

        child_child_env = child_env.spawn()

        self.assertEqual(child_child_env.reply("_"), 3)
        self.assertEqual(child_child_env.upload_doc(b"_"), 2)

        other_child_env = env.spawn()

        self.assertEqual(other_child_env.reply("_"), 1)
        self.assertEqual(other_child_env.upload_doc(b"_"), 2)

    def test_spawn(self):
        env = Environment("manager")
        inner_env = env.spawn()

        self.assertEqual(env.manager, inner_env.manager)
        self.assertEqual(env.parent, None)
        self.assertEqual(inner_env.parent, env)

    def test_failed_method_replace(self):
        env = Environment("manager")

        with self.assertRaises(ValueError):
            env.replace_method("no_method_with_that_name", lambda: 1)

    def test_failed_setattr(self):
        env = Environment("manager")

        with self.assertRaises(AttributeError):
            env.reply = 1

        with self.assertRaises(AttributeError):
            setattr(env, "reply", 1)

    def test_concrete_environment(self):
        env1 = VKEnvironment("vk")
        env2 = TGEnvironment("tg")

        env1.replace_method("reply", print)
        env1.a = 10

        child1 = env1.spawn()

        self.assertEqual(child1.a, 10)
        self.assertEqual(child1.reply.func, print)

        env2.replace_method("reply", print)
        env2.a = 10

        child2 = env2.spawn()

        self.assertEqual(child2.a, 10)
        self.assertEqual(child2.reply.func, print)

        child2.a = 20

        child_child2 = child2.spawn()

        self.assertEqual(child_child2.a, 20)
        self.assertEqual(env2.a, 10)


