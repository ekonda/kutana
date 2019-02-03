import asyncio
import logging
import unittest

from kutana import (BasicManager, DebugEnvironment, DebugManager, Executor,
                    Plugin, VKEnvironment, VKManager, VKResponse, load_plugins,
                    load_value, set_logger_level)


class TestMiscellaneous(unittest.TestCase):
    def test_load_plugins(self):
        loaded_plugins = load_plugins("test/test_plugins/")
        loaded_plugins.sort(key=lambda plugin: plugin.name)

        self.assertEqual(len(loaded_plugins), 2)

        self.assertEqual(loaded_plugins[0].name, "Memory")
        self.assertEqual(loaded_plugins[1].name, "My file")

        executor = Executor()
        executor.register_plugins(loaded_plugins)

        loop = asyncio.get_event_loop()

        loop.run_until_complete(executor.startup(None))

        loop.run_until_complete(
            executor.process(
                "message", DebugEnvironment(DebugManager(), peer_id=0)
            )
        )

        self.assertEqual(loaded_plugins[0].memory, "message")
        self.assertEqual(loaded_plugins[1].my_file, ":)")

    def test_load_value(self):
        value = load_value("key", "test/test_assets/sample.json")

        self.assertEqual(value, "value")

        value = load_value("key2", "test/test_assets/sample.json")

        self.assertEqual(value, {"keynkey": "hvalue"})

    def test_split_large_text(self):
        split = BasicManager.split_large_text

        self.assertEqual(split("abc"), ("abc",))

        parts = split("abc" * 4096)

        self.assertEqual(parts[0], ("abc" * 4096)[:4096])
        self.assertEqual(len(parts), 3)

    def test_plugin_with_exception_callback(self):
        plugin = Plugin(exceptions=0)

        async def on_text(message, env):
            raise Exception

        plugin.on_has_text()(on_text)

        def _prepare_callbacks_error():
            async def callback(update, env):
                plugin.exceptions += 1  # pylint: disable=E1101

            return (callback,)

        plugin._prepare_callbacks_error = _prepare_callbacks_error

        executor = Executor()

        executor.register_plugins([plugin])

        loop = asyncio.get_event_loop()

        set_logger_level(logging.CRITICAL)

        loop.run_until_complete(
            executor.process(
                "message", DebugEnvironment(DebugManager(), peer_id=0)
            )
        )

        set_logger_level(logging.ERROR)

        self.assertEqual(plugin.exceptions, 1)  # pylint: disable=E1101

    def test_vk_conversation(self):
        class FakeManager(VKManager):
            def __init__(self):
                pass

            async def request(self, method, **kwargs):
                return VKResponse(False, (), {"object_id": 1})

        env = VKEnvironment(FakeManager(), peer_id=0)

        loop = asyncio.get_event_loop()

        message = loop.run_until_complete(
            env.manager.create_message(
                {"object": {"date": 1, "random_id": 0, "fwd_messages": [],
                "important": False, "peer_id": 1,
                "text": "echo [club1|\u0421\u043e] 123", "attachments": [],
                "conversation_message_id": 1411, "out": 0, "from_id": 1,
                "id": 0, "is_hidden": False}, "group_id": 1,
                "type": "message_new"}
            )
        )

        self.assertEqual(message.text, "echo  123")
        self.assertEqual(message.attachments, ())

        message = loop.run_until_complete(
            env.manager.create_message(
                {"object": {"date": 1, "random_id": 0, "fwd_messages": [],
                "important": False, "peer_id": 1,
                "text": "echo [club1|\u0421\u043e] 123", "attachments": [],
                "conversation_message_id": 1411, "out": 0, "from_id": 1,
                "id": 0, "is_hidden": False}, "group_id": 2,
                "type": "message_new"}
            )
        )

        self.assertEqual(message.text, "echo [club1|\u0421\u043e] 123")
        self.assertEqual(message.attachments, ())


if __name__ == '__main__':
    unittest.main()
