from unittest.mock import MagicMock

import pytest

from kutana.handler import PROCESSED, SKIPPED
from kutana.router import CommandsRouter, ListRouter, MapRouter
from kutana.update import Message


def test_merge_ok():
    r1 = ListRouter()
    r2 = ListRouter()

    assert ListRouter.merge([r1, r2])


def test_merge_mixed_classes():
    r1 = ListRouter()
    r2 = MapRouter()

    with pytest.raises(ValueError):
        ListRouter.merge([r1, r2])


def test_merge_mixed_priorities():
    r1 = ListRouter(priority=1)
    r2 = ListRouter(priority=2)

    r3 = ListRouter.merge([r1, r2])

    with pytest.raises(ValueError):
        ListRouter.merge([r3, r2])


async def test_list_router():
    r = ListRouter()

    async def _return_skipped(upd, ctx):
        return SKIPPED

    r.add_handler(_return_skipped)

    assert await r.handle("upd", "ctx") == SKIPPED

    async def _return_processed(upd, ctx):
        return PROCESSED

    r.add_handler(_return_processed)

    assert await r.handle("upd", "ctx") == PROCESSED


async def test_commands_router():
    r = CommandsRouter()

    def _get_context(message):
        return MagicMock(
            app=MagicMock(config={"prefixes": ["/"]}),
            update=MagicMock(spec=Message, text=message),
        )

    async def _return_skipped(upd, ctx):
        return SKIPPED

    r.add_handler("skipped", _return_skipped)

    assert await r.handle("upd", _get_context("/skipped")) == SKIPPED
    assert await r.handle("upd", _get_context("/processed")) == SKIPPED

    async def _return_processed(upd, ctx):
        return PROCESSED

    r.add_handler("processed", _return_processed)

    assert await r.handle("upd", _get_context("/skipped")) == SKIPPED
    assert await r.handle("upd", _get_context("/processed")) == PROCESSED
