import asyncio
import pytest
from asynctest.mock import patch
from kutana import Kutana, Plugin
from kutana.storage import OptimisticLockException
from kutana.storages import MemoryStorage
from kutana.backends import Debug
from testing_tools import make_kutana


def test_happy_path():
    app = Kutana()

    # Simple echo plugin
    pl = Plugin("")

    @pl.on_messages()
    async def __(message, ctx):
        await ctx.reply(message.text)

    app.add_plugin(pl)

    # Simple debug backend
    debug = Debug(
        messages=[("message 1", 1), ("message 2", 2)],
        on_complete=app.stop,
    )

    app.add_backend(debug)

    # Run application
    app.run()

    # Check replies
    assert debug.answers[1] == [("message 1", (), {})]
    assert debug.answers[2] == [("message 2", (), {})]


def test_add_plugins():
    added = []

    app = Kutana()
    assert app.get_plugins() == []

    app.add_plugin = lambda pl: added.append(pl)
    app.add_plugins(["a", "b", "c"])
    assert added == ["a", "b", "c"]


def test_get_loop():
    app = Kutana()
    assert app._loop == app.get_loop()


def test_same_plugins_and_backends():
    app = Kutana()

    plugin = Plugin("")
    backend = Debug([])

    app.add_plugin(plugin)
    with pytest.raises(RuntimeError):
        app.add_plugin(plugin)

    app.add_backend(backend)
    with pytest.raises(RuntimeError):
        app.add_backend(backend)

    assert app.get_backends() == [backend]

def test_incorrect_values():
    app = Kutana()

    with pytest.raises(ValueError):
        app.add_backend(None)

    with pytest.raises(ValueError):
        app.set_storage('permanent', None)

    with pytest.raises(ValueError):
        app.add_plugin(None)



def test_storages():
    app = Kutana()

    app.set_storage('permanent', MemoryStorage())

    assert app.get_storage('default')
    assert app.get_storage('permanent')
    assert not app.get_storage('temporary')


def test_not_active_backend():
    app = Kutana()
    app.add_backend(Debug([], name="backend1", active=False))

    async def test():
        with patch('asyncio.ensure_future') as ensure_future:
            await app._on_start(None)
            ensure_future.assert_not_called

    asyncio.get_event_loop().run_until_complete(test())


def test_get_backend():
    app = Kutana()
    app.add_backend(Debug([], name="backend1"))
    app.add_backend(Debug([], name="backend2"))

    assert app.get_backend("backend1").name == "backend1"
    assert app.get_backend("backend2").name == "backend2"
    assert app.get_backend("backend3") is None


def test_add_backend():
    app = Kutana()

    with pytest.raises(ValueError):
        app.add_backend(None)


def test_start_and_shutdown_hooks():
    app, _ = make_kutana([("123", 1), ("321", 1)])

    called = []

    pl = Plugin("")

    @pl.on_start()
    async def __(app):
        called.append("start")

    @pl.on_messages()
    async def __(msg, ctx):
        await ctx.reply("ok")

    @pl.on_shutdown()
    async def __(app):
        called.append("shutdown")

    app.add_plugin(pl)

    app.run()

    assert called == ["start", "shutdown"]


def test_before_and_after_hooks():
    app, _ = make_kutana([("123", 1), ("321", 1)])

    called = []
    saved_ctxs = []

    pl = Plugin("")

    @pl.on_before()
    async def __(update, ctx):
        called.append("before")
        saved_ctxs.append(ctx)

    @pl.on_messages()
    async def __(msg, ctx):
        await ctx.reply("ok")
        called.append("handle")

    @pl.on_after()
    async def __(update, ctx, r):
        called.append("after")
        saved_ctxs.append(ctx)

    app.add_plugin(pl)

    app.run()

    assert called == ["before", "handle", "after"] * 2
    assert saved_ctxs[0] is saved_ctxs[1]


def test_exception_hooks():
    called = []

    app, _ = make_kutana([("123", 1), ("321", 1)])

    pl = Plugin("")

    @pl.on_messages()
    async def __(msg, ctx):
        called.append("bruh")
        await ctx.reply("bruh")
        raise Exception("bruh")

    @pl.on_exception()
    async def __(update, ctx, exc):
        called.append("exception")
        assert exc == Exception
        assert str(exc) == "bruh"

    @pl.on_after()
    async def __(update, ctx, r):
        called.append("after")

    app.add_plugin(pl)

    app.run()

    assert called == ["bruh", "exception"] * 2


def test_routers_merge():
    app, backend = make_kutana([("123", 1), ("321", 1)])

    pl1 = Plugin("")

    @pl1.on_match("123")
    async def __(msg, ctx):
        await ctx.reply("ok1")

    app.add_plugin(pl1)

    pl2 = Plugin("")

    @pl2.on_match("321")
    async def __(msg, ctx):
        await ctx.reply("ok2")

    app.add_plugin(pl2)

    app.run()

    assert len(app._routers) == 1
    assert backend.answers[1] == [("ok1", (), {}), ("ok2", (), {})]


def test_handler_with_exception():
    app, _ = make_kutana([("msg1", 1), ("msg2", 2), ("msg3", 3)])

    pl = Plugin("")

    @pl.on_match("msg1")
    async def __(message, ctx):
        await ctx.reply("ok")
        raise asyncio.CancelledError

    @pl.on_match("msg2")
    async def __(message, ctx):
        await ctx.reply("ok")
        raise Exception

    @pl.on_match("msg3")
    async def __(message, ctx):
        await ctx.reply("ok")
        raise OptimisticLockException

    app.add_plugin(pl)

    app.run()


def test_kutana_shutdown():
    app = Kutana()

    async def trigger():
        raise KeyboardInterrupt

    _shutdown = app._shutdown
    async def checker():
        checker._called = True
        await _shutdown()
    checker._called = False

    app._main_loop = trigger
    app._shutdown = checker
    app.run()

    assert checker._called == True
