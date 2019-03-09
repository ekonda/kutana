import logging

from kutana import set_logger_level

from testing_tools import KutanaTest


logging.disable(logging.INFO)


class TestKutana(KutanaTest):
    def test_debug(self):
        self.target = ["message"]

        with self.debug_manager(self.target):

            async def new_update(update, env):
                await env.reply(update)

            self.app.register(new_update)

    def test_debug_upload(self):
        self.target = ["file"]

        with self.debug_manager(self.target):

            async def new_update(update, env):
                attachment = await env.upload_doc("file")

                await env.reply("", attachment=attachment)

            self.app.register(new_update)

    def test_priority(self):
        self.called_1 = 0
        self.called_2 = 0

        with self.debug_manager(["message"]):

            async def prc1(update, env):
                self.called_1 += 1
                return "DONE"

            async def prc2(update, env):
                self.called_2 += 1
                return "DONE"

            self.app.register(prc1)
            self.app.register(prc2, priority=10)

        self.assertEqual(self.called_1, 0)
        self.assertEqual(self.called_2, 1)

    def test_exception(self):
        self.called = 0

        self.target = ["Произошла крайне критическая ошибка. "
                       "Сообщите об этом администратору."]

        with self.debug_manager(["message"]):

            async def new_update(update, env):
                async def just_raise(update, env):
                    self.called += 1
                    raise Exception

                env.register_after_processed(just_raise)

                raise Exception

            self.app.register(new_update)

            set_logger_level(logging.CRITICAL)

        set_logger_level(logging.ERROR)

        self.assertEqual(self.called, 1)

    def test_no_default_exception_handle(self):
        self.target = []

        with self.debug_manager(["message"]):

            async def new_update(update, env):
                raise Exception

            self.app.register(new_update)

            set_logger_level(logging.CRITICAL)

        set_logger_level(logging.ERROR)
