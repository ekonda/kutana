from kutana import Plugin

from testing_tools import KutanaTest


class TestPlugins(KutanaTest):
    def test_plugin_on_text_exception(self):
        plugin = Plugin()

        with self.assertRaises(ValueError):
            plugin.on_text()

    def test_plugin_on_after_processed_exception(self):
        plugin = Plugin()

        with self.assertRaises(ValueError):
            plugin.on_after_processed(messages=False, updates=False)

    def test_plugin_on_after_processed(self):
        plugin = Plugin()

        plugin.on_after_processed(messages=True, updates=False)(1)

        self.assertTrue(plugin._callbacks)
        self.assertFalse(plugin._callbacks_raw)

        plugin = Plugin()

        plugin.on_after_processed(messages=False, updates=True)(1)

        self.assertFalse(plugin._callbacks)
        self.assertTrue(plugin._callbacks_raw)

        plugin = Plugin()

        plugin.on_after_processed(messages=True, updates=True)(1)

        self.assertTrue(plugin._callbacks)
        self.assertTrue(plugin._callbacks_raw)
