import pytest
from kutana import Context
from kutana.handler import Handler
from kutana.router import Router, ListRouter, MapRouter


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
