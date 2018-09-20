from kutana import logger
from test_framework import KutanaTest
import logging


logging.disable(logging.INFO)


class TestExecutors(KutanaTest):
    def tearDown(self):
        logger.setLevel(logging.ERROR)

    def test_just_debug(self):
        self.target = ["message"] * 5

        with self.debug_controller(self.target):

            async def new_update(update, eenv):
                if eenv.ctrl_type == "debug":
                    await eenv.reply(update)

                else:
                    self.assertEqual(eenv.ctrl_type, "kutana")

            self.kutana.executor.register(new_update)

    def test_debug_upload(self):
        self.target = ["file"]

        with self.debug_controller(self.target):

            async def new_update(update, eenv):
                if eenv.ctrl_type == "debug":
                    attachment = await eenv.upload_doc("file")
                    await eenv.reply("", attachment=attachment)

                else:
                    self.assertEqual(eenv.ctrl_type, "kutana")

            self.kutana.executor.register(new_update)

    def test_priority(self):
        self.called_1 = 0
        self.called_2 = 0

        with self.debug_controller(["message", "message"]):

            async def prc1(update, eenv):
                if eenv.ctrl_type == "debug":
                    self.called_1 += 1
                    return "DONE"

            prc1.priority = 0  # very low

            async def prc2(update, eenv):
                if eenv.ctrl_type == "debug":
                    self.called_2 += 1
                    return "DONE"

            self.kutana.executor.register(prc1)
            self.kutana.executor.register(prc2, priority=1000)  # very high

        self.assertEqual(self.called_1, 0)
        self.assertEqual(self.called_2, 2)

    def test_exception(self):
        self.called = 0

        with self.debug_controller(["message"] * 5):

            async def new_update(update, eenv):
                if eenv.ctrl_type == "debug":
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

        with self.debug_controller(["message"] * 5):

            async def new_update(update, eenv):
                if eenv.ctrl_type == "debug":
                    eenv.reply = my_faked_reply
                    raise Exception

            self.kutana.executor.register(new_update)

            logger.setLevel(logging.CRITICAL)

        self.assertEqual(self.called, 5)


    def test_two_debug(self):
        self.target = ["message"] * 5
        self.called = 0

        with self.debug_controller(self.target):
            with self.debug_controller(self.target):

                async def new_update(update, eenv):
                    if eenv.ctrl_type == "debug":
                        await eenv.reply(update)
                        self.called += 1

                    else:
                        self.assertEqual(eenv.ctrl_type, "kutana")

                self.kutana.executor.register(new_update)

        self.assertEqual(self.called, 10)

    def test_two_callbacks_and_two_debugs(self):
            self.target = ["message"] * 5
            self.called = 0

            with self.debug_controller(self.target):
                with self.debug_controller(self.target):
                    self.target *= 2

                    async def new_update_1(update, eenv):
                        if eenv.ctrl_type == "debug":
                            await eenv.reply(update)
                            self.called += 1

                    async def new_update_2(update, eenv):
                        if eenv.ctrl_type == "debug":
                            await eenv.reply(update)
                            self.called += 1

                    self.kutana.executor.register(new_update_1)
                    self.kutana.executor.register(new_update_2)

            self.assertEqual(self.called, 20)

    def test_decorate_or_call(self):
        self.target = ["message"] * 5

        with self.debug_controller(self.target):
            self.target *= 2

            @self.kutana.executor.register()
            async def new_update(update, eenv):
                if eenv.ctrl_type == "debug":
                    await eenv.reply(update)

            self.kutana.executor.register(new_update)
