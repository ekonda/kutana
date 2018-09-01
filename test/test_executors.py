from test_framework import KutanaTest
import logging


logging.disable(logging.CRITICAL)


class TestExecutors(KutanaTest):
    def test_just_dumping(self):
        self.target = ["message"] * 10

        with self.dumping_controller(self.target):

            async def new_update(controller_type, update, env):
                if controller_type == "dumping":
                    self.actual.append(update)

                else:
                    self.assertEqual(controller_type, "kutana")

            self.kutana.executor.register(new_update)

    def test_exception(self):
        self.called = 0

        with self.dumping_controller(["message"] * 10):

            async def new_update(controller_type, update, env):
                if controller_type == "dumping":
                    raise Exception

            self.kutana.executor.register(new_update)

            async def new_error(controller_type, update, env):
                self.called += 1

            self.kutana.executor.register(new_error, error=True)

        self.assertEqual(self.called, 10)

    def test_two_dumping(self):
        self.target = ["message"] * 10

        with self.dumping_controller(self.target):
            with self.dumping_controller(self.target):
                self.target *= 2

                async def new_update(controller_type, update, env):
                    if controller_type == "dumping":
                        self.actual.append(update)

                    else:
                        self.assertEqual(controller_type, "kutana")

                self.kutana.executor.register(new_update)

    def test_two_callbacks_and_two_dumpings(self):
            self.target = ["message"] * 10

            with self.dumping_controller(self.target):
                with self.dumping_controller(self.target):
                    self.target *= 4

                    async def new_update_1(controller_type, update, env):
                        if controller_type == "dumping":
                            self.actual.append(update)

                    async def new_update_2(controller_type, update, env):
                        if controller_type == "dumping":
                            self.actual.append(update)

                    self.kutana.executor.register(new_update_1)
                    self.kutana.executor.register(new_update_2)

    def test_decorate_or_call(self):
        self.target = ["message"] * 10

        with self.dumping_controller(self.target):
            self.target *= 2

            @self.kutana.executor.register()
            async def new_update(controller_type, update, env):
                if controller_type == "dumping":
                    self.actual.append(update)

            self.kutana.executor.register(new_update)
