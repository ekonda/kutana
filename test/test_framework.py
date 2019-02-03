import unittest
from contextlib import contextmanager

from kutana import DebugManager, Kutana, Plugin


class KutanaTest(unittest.TestCase):
    def setUp(self):
        self.kutana = None
        self.target = []

    @contextmanager
    def debug_manager(self, queue):
        if self.kutana is None:
            self.kutana = Kutana()

        self.manager = DebugManager(*queue)

        self.kutana.add_manager(self.manager)

        self.plugin = Plugin()

        self.plugins = [self.plugin]

        try:
            yield self.plugin
        finally:
            for plugin in self.plugins:
                self.kutana.executor.register_plugins([plugin])

            self.kutana.run()

        self.assertEqual(self.target, self.manager.replies)
