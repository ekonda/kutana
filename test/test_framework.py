from kutana import Kutana, DebugController, Plugin
from contextlib import contextmanager
import unittest


class KutanaTest(unittest.TestCase):
    def setUp(self):
        self.kutana = None
        self.target = []

    @contextmanager
    def debug_controller(self, queue):
        if self.kutana is None:
            self.kutana = Kutana()

        self.controller = DebugController(*queue)

        self.kutana.add_controller(self.controller)

        self.plugin = Plugin()

        self.plugins = [self.plugin]

        try:
            yield self.plugin
        finally:
            for plugin in self.plugins:
                self.kutana.executor.register_plugins(plugin)

            self.kutana.run()

        self.assertEqual(self.target, self.controller.replies)
