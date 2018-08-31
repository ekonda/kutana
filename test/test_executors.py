from kutana import Kutana, DumpingController, Plugin
from contextlib import contextmanager
from test_framework import KutanaTest
import unittest


class TestExecutors(KutanaTest):
    def test_just_dumping(self):
        self.target = ["message"] * 10

        with self.dumping_controller(self.target):

            @self.kutana.executor.register()
            async def new_update(controller_type, update, env):
                if controller_type == "dumping":
                    self.actual.append(update)

                else:
                    self.assertEqual(controller_type, "kutana")

    def test_two_dumping(self):
        self.target = ["message"] * 10

        with self.dumping_controller(self.target):
            with self.dumping_controller(self.target):
                self.target += self.target

                @self.kutana.executor.register()
                async def new_update(controller_type, update, env):
                    if controller_type == "dumping":
                        self.actual.append(update)

                    else:
                        self.assertEqual(controller_type, "kutana")

    def test_two_callbacks_and_two_dumpings(self):
            self.target = ["message"] * 10

            with self.dumping_controller(self.target):
                with self.dumping_controller(self.target):
                    self.target *= 4

                    @self.kutana.executor.register()
                    async def new_update_1(controller_type, update, env):
                        if controller_type == "dumping":
                            self.actual.append(update)

                    @self.kutana.executor.register()
                    async def new_update_2(controller_type, update, env):
                        if controller_type == "dumping":
                            self.actual.append(update)