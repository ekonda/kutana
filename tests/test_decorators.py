from unittest.mock import MagicMock, AsyncMock

import pytest

from kutana import PROCESSED, SKIPPED, RecipientKind
from kutana.decorators import expect_backend, expect_recipient_kind, expect_sender_is_admin, expect_sender_is_owner


async def test_expect_backend():
    async def _return_processed(*_):
        return PROCESSED

    funciton = expect_backend("vk")(_return_processed)

    context_from_vk = MagicMock(backend=MagicMock(get_identity=MagicMock(return_value="vk")))
    assert await funciton(MagicMock(), context_from_vk) == PROCESSED

    context_from_tg = MagicMock(backend=MagicMock(get_identity=MagicMock(return_value="tg")))
    assert await funciton(MagicMock(), context_from_tg) == SKIPPED


async def test_expect_recipient_kind():
    async def _return_processed(*_):
        return PROCESSED

    funciton = expect_recipient_kind(RecipientKind.GROUP_CHAT)(_return_processed)

    message_from_group_chat = MagicMock(recipient_kind=RecipientKind.GROUP_CHAT)
    assert await funciton(message_from_group_chat, MagicMock()) == PROCESSED

    message_from_private_chat = MagicMock(recipient_kind=RecipientKind.PRIVATE_CHAT)
    assert await funciton(message_from_private_chat, MagicMock()) == SKIPPED


async def _test_expect_sender(decorator, results):
    async def _return_processed(*_):
        return PROCESSED

    funciton = decorator()(_return_processed)

    message = MagicMock(
        recipient_id=1000,
        sender_id=3,
        recipient_kind=RecipientKind.GROUP_CHAT,
    )

    # --- vk ---
    context_from_vk = MagicMock(
        backend=MagicMock(
            get_identity=MagicMock(return_value="vk"),
            request=AsyncMock(return_value={"items": [{"member_id": 3, "is_owner": True}]}),
        )
    )
    assert await funciton(message, context_from_vk) == results[0]

    context_from_vk = MagicMock(
        backend=MagicMock(
            get_identity=MagicMock(return_value="vk"),
            request=AsyncMock(return_value={"items": [{"member_id": 3, "is_admin": True}]}),
        )
    )
    assert await funciton(message, context_from_vk) == results[1]

    context_from_vk = MagicMock(
        backend=MagicMock(
            get_identity=MagicMock(return_value="vk"),
            request=AsyncMock(return_value={"items": [{"member_id": 3}]}),
        )
    )
    assert await funciton(message, context_from_vk) == results[2]

    assert await funciton(MagicMock(recipient_kind=RecipientKind.PRIVATE_CHAT), context_from_vk) == SKIPPED

    # --- tg ---
    context_from_tg = MagicMock(
        backend=MagicMock(
            get_identity=MagicMock(return_value="tg"),
            request=AsyncMock(return_value=[{"user": {"id": 3}, "status": "creator"}]),
        )
    )
    assert await funciton(message, context_from_tg) == results[3]

    context_from_tg = MagicMock(
        backend=MagicMock(
            get_identity=MagicMock(return_value="tg"),
            request=AsyncMock(return_value=[{"user": {"id": 3}, "status": "administrator"}]),
        )
    )
    assert await funciton(message, context_from_tg) == results[4]

    context_from_tg = MagicMock(
        backend=MagicMock(
            get_identity=MagicMock(return_value="tg"),
            request=AsyncMock(return_value=[]),
        )
    )
    assert await funciton(message, context_from_tg) == results[5]

    assert await funciton(MagicMock(recipient_kind=RecipientKind.PRIVATE_CHAT), context_from_tg) == SKIPPED

    # --- other backend ---
    context_from_bruh = MagicMock(backend=MagicMock(get_identity=MagicMock(return_value="bruh")))

    with pytest.raises(NotImplementedError):
        await funciton(message, context_from_bruh)

    assert await funciton(MagicMock(recipient_kind=RecipientKind.PRIVATE_CHAT), context_from_bruh) == SKIPPED


async def test_expect_sender_is_admin():
    await _test_expect_sender(
        expect_sender_is_admin,
        [
            PROCESSED,
            PROCESSED,
            SKIPPED,
            PROCESSED,
            PROCESSED,
            SKIPPED,
        ],
    )


async def test_expect_sender_is_owner():
    await _test_expect_sender(
        expect_sender_is_owner,
        [
            PROCESSED,
            SKIPPED,
            SKIPPED,
            PROCESSED,
            SKIPPED,
            SKIPPED,
        ],
    )
