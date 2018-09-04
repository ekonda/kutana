from kutana import Executor, logger
from test_framework import KutanaTest
import logging


logging.disable(logging.INFO)


class TestExecutors(KutanaTest):
    def tearDown(self):
        logger.setLevel(logging.ERROR)

    def test_just_dumping(self):
        self.target = ["message"] * 5

        with self.dumping_controller(self.target):

            async def new_update(update, eenv):
                if eenv.ctrl_type == "dumping":
                    self.actual.append(update)

                else:
                    self.assertEqual(eenv.ctrl_type, "kutana")

            self.kutana.executor.register(new_update)

    def test_exception(self):
        self.called = 0

        with self.dumping_controller(["message"] * 5):

            async def new_update(update, eenv):
                if eenv.ctrl_type == "dumping":
                    raise Exception

            self.kutana.executor.register(new_update)

            async def new_error(update, eenv):
                self.assertTrue(eenv.exception)

                self.called += 1

                return "DONE"

            async def new_error_no(update, eenv):
                self.assertTrue(False)

            self.kutana.executor.register(new_error, error=True)
            self.kutana.executor.register(new_error_no, error=True)

            logger.setLevel(logging.CRITICAL)

        self.assertEqual(self.called, 5)

    def test_default_exception_handle(self):
        self.called = 0

        async def my_faked_reply(mes):
            self.assertEqual(mes, "Произошла ошибка! Приносим свои извинения.")
            self.called += 1

        with self.dumping_controller(["message"] * 5):

            async def new_update(update, eenv):
                if eenv.ctrl_type == "dumping":
                    eenv.reply = my_faked_reply
                    raise Exception

            self.kutana.executor.register(new_update)

            logger.setLevel(logging.CRITICAL)

        self.assertEqual(self.called, 5)


    def test_two_dumping(self):
        self.target = ["message"] * 5

        with self.dumping_controller(self.target):
            with self.dumping_controller(self.target):
                self.target *= 2

                async def new_update(update, eenv):
                    if eenv.ctrl_type == "dumping":
                        self.actual.append(update)

                    else:
                        self.assertEqual(eenv.ctrl_type, "kutana")

                self.kutana.executor.register(new_update)

    def test_two_callbacks_and_two_dumpings(self):
            self.target = ["message"] * 5

            with self.dumping_controller(self.target):
                with self.dumping_controller(self.target):
                    self.target *= 4

                    async def new_update_1(update, eenv):
                        if eenv.ctrl_type == "dumping":
                            self.actual.append(update)

                    async def new_update_2(update, eenv):
                        if eenv.ctrl_type == "dumping":
                            self.actual.append(update)

                    self.kutana.executor.register(new_update_1)
                    self.kutana.executor.register(new_update_2)

    def test_decorate_or_call(self):
        self.target = ["message"] * 5

        with self.dumping_controller(self.target):
            self.target *= 2

            @self.kutana.executor.register()
            async def new_update(update, eenv):
                if eenv.ctrl_type == "dumping":
                    self.actual.append(update)

            self.kutana.executor.register(new_update)

    def test_merge_executors(self):
        exec1 = Executor()
        exec2 = Executor()

        async def cor1(*args, **kwargs):
            pass

        async def cor2(*args, **kwargs):
            pass

        exec1.register(cor1)
        exec2.register(cor2)

        exec1.callbacks_owners.append(1)
        exec2.callbacks_owners.append(2)

        exec1.add_callbacks_from(exec2)

        self.assertEqual(exec1.callbacks, [cor1, cor2])
        self.assertEqual(exec1.error_callbacks, [])
        self.assertEqual(exec1.callbacks_owners, [1, 2])
