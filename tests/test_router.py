import pytest
from kutana import Context
from kutana.handler import Handler
from kutana.router import Router, ListRouter, MapRouter
from kutana.routers import AnyMessageRouter, AnyUnprocessedMessageRouter


def test_check():
    r = Router()
    h = Handler(None, "", "", 0)

    c = Context()
    c.group_state = ""
    c.user_state = ""

    assert r._check(h, None, c)

    c.group_state = ""
    c.user_state = "state"
    assert not r._check(h, None, c)


def test_exception_on_wrong_merge():
    lr = ListRouter()
    mr = MapRouter()

    with pytest.raises(RuntimeError):
        lr.merge(mr)

    with pytest.raises(RuntimeError):
        mr.merge(lr)


def test_multiple_handlers():
    mr = MapRouter()

    mr.add_handler(Handler(1, "*", "*", 0), "a")
    mr.add_handler(Handler(2, "*", "*", 0), "a")
    mr.add_handler(Handler(3, "*", "*", 0), "a")

    assert len(mr._handlers["a"]) == 3


def test_router_merge():
    mr1 = MapRouter()
    mr2 = MapRouter()

    mr1.add_handler(Handler(1, "*", "*", 0), "a")
    mr1.add_handler(Handler(2, "*", "*", 0), "b")
    mr2.add_handler(Handler(3, "*", "*", 0), "a")

    mr1.merge(mr2)

    assert len(mr1._handlers["a"]) == 2
    assert len(mr1._handlers["b"]) == 1


def test_router_subclass_merge():
    mr1 = AnyMessageRouter()
    mr2 = AnyUnprocessedMessageRouter()
    mr3 = ListRouter()
    mr4 = AnyMessageRouter()

    mr1.add_handler(Handler(1, "*", "*", 0))
    mr1.add_handler(Handler(2, "*", "*", 0))
    mr2.add_handler(Handler(3, "*", "*", 0))
    mr3.add_handler(Handler(4, "*", "*", 0))
    mr4.add_handler(Handler(5, "*", "*", 0))

    with pytest.raises(RuntimeError):
        mr1.merge(mr2)

    with pytest.raises(RuntimeError):
        mr1.merge(mr3)

    with pytest.raises(RuntimeError):
        mr2.merge(mr3)

    mr4.merge(mr1)

    assert len(mr1._handlers) == 2
    assert len(mr2._handlers) == 1
    assert len(mr3._handlers) == 1
    assert len(mr4._handlers) == 3
    assert set(map(lambda h: h.handle, mr4._handlers)) == {5, 1, 2}


def test_router_merge_priority():
    mr1 = AnyMessageRouter(priority=9)
    mr2 = AnyMessageRouter(priority=7)
    mr3 = AnyMessageRouter(priority=5)
    mr4 = AnyMessageRouter(priority=5)

    mr1.add_handler(Handler(1, "*", "*", 0))
    mr2.add_handler(Handler(2, "*", "*", 0))
    mr3.add_handler(Handler(3, "*", "*", 0))
    mr3.add_handler(Handler(4, "*", "*", 5))
    mr4.add_handler(Handler(5, "*", "*", 3))
    mr4.add_handler(Handler(6, "*", "*", 10))

    with pytest.raises(RuntimeError):
        mr1.merge(mr2)

    with pytest.raises(RuntimeError):
        mr1.merge(mr3)

    with pytest.raises(RuntimeError):
        mr2.merge(mr3)

    mr3.merge(mr4)

    handlers = list(map(lambda h: h.handle, [
        *mr1._handlers,
        *mr2._handlers,
        *mr3._handlers,
    ]))

    assert handlers == [1, 2, 6, 4, 5, 3]
