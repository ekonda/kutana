import logging

from kutana import set_logger_level

from test_framework import KutanaTest


logging.disable(logging.INFO)


class TestExecutors(KutanaTest):
    def tearDown(self):
        set_logger_level(logging.ERROR)

    def test_just_debug(self):
        self.target = ["message"]

        with self.debug_manager(self.target):

            async def new_update(update, env):
                await env.reply(update)

            self.kutana.executor.register(new_update)

    def test_debug_upload(self):
        self.target = ["file"]

        with self.debug_manager(self.target):

            async def new_update(update, env):
                attachment = await env.upload_doc("file")

                await env.reply("", attachment=attachment)

            self.kutana.executor.register(new_update)

    def test_priority(self):
        self.called_1 = 0
        self.called_2 = 0

        with self.debug_manager(["message"]):

            async def prc1(update, env):
                self.called_1 += 1
                return "DONE"

            prc1.priority = 0  # very low

            async def prc2(update, env):
                self.called_2 += 1
                return "DONE"

            self.kutana.executor.register(prc1)
            self.kutana.executor.register(prc2, priority=1000)  # very high

        self.assertEqual(self.called_1, 0)
        self.assertEqual(self.called_2, 1)

    def test_exception(self):
        self.called = 0

        with self.debug_manager(["message"]):

            async def new_update(update, env):
                if env.manager_type == "debug":
                    raise Exception

            self.kutana.executor.register(new_update)

            async def new_error(update, env):
                self.assertTrue(env.exception)

                self.called += 1

                return "DONE"

            async def new_error_no(update, env):
                self.assertTrue(False)

            self.kutana.executor.register(new_error, error=True)
            self.kutana.executor.register(new_error_no, error=True)

            set_logger_level(logging.CRITICAL)

        self.assertEqual(self.called, 1)

    def test_default_exception_handle(self):
        self.target = ["Произошла ошибка! Приносим свои извинения."]

        with self.debug_manager(["message"]):

            async def new_update(update, env):
                raise Exception

            self.kutana.executor.register(new_update)

            set_logger_level(logging.CRITICAL)

    def test_decorate_or_call(self):
        self.target = ["message"]

        with self.debug_manager(self.target):

            self.target *= 2

            @self.kutana.executor.register()
            async def new_update(update, env):
                await env.reply(update)

            self.kutana.executor.register(new_update)
