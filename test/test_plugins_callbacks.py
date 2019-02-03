from kutana import Plugin

from test_framework import KutanaTest


class TestPlugins(KutanaTest):
    def test_plugin_on_text_exception(self):
        plugin = Plugin()

        with self.assertRaises(ValueError):
            plugin.on_text()
