from kutana import Kutana, DumpingController, Plugin
from contextlib import contextmanager
import unittest


class KutanaTest(unittest.TestCase):
    def setUp(self):
        self.kutana = None

        self.target = []
        self.actual = []

    @contextmanager
    def dumping_controller(self, queue):
        if self.kutana is None:
            self.kutana = Kutana()

        self.controller = DumpingController(*queue)

        self.kutana.add_controller(self.controller)

        self.plugin = Plugin()

        self.plugins = [self.plugin]

        try:
            yield self.plugin
        finally:
            for plugin in self.plugins:
                self.kutana.executor.register_plugins(plugin)

            self.kutana.run()

        self.assertEqual(self.target, self.actual)
