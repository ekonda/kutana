import unittest
from contextlib import contextmanager

from kutana import DebugManager, Kutana, Plugin


class KutanaTest(unittest.TestCase):
    def setUp(self):
        self.app = None
        self.target = []

    @contextmanager
    def debug_manager(self, queue):
        if self.app is None:
            self.app = Kutana()

        self.manager = DebugManager(*queue)

        self.app.add_manager(self.manager)

        self.plugin = Plugin()

        self.plugins = [self.plugin]

        try:
            yield self.plugin
        finally:
            for plugin in self.plugins:
                self.app.register_plugins([plugin])

            self.app.run()

        self.assertEqual(self.target, self.manager.replies)
