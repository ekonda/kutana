from functools import wraps

from .backend import Backend
from .context import Context
from .handler import SKIPPED
from .update import Message, RecipientKind


def expect_recipient_kind(expected_recipient_kind: RecipientKind):
    """
    Return decorators that skips all messages with "recipient_kind"
    different from specified one.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, context: Context):
            if message.recipient_kind != expected_recipient_kind:
                return SKIPPED
            return await func(message, context)

        return wrapper

    return decorator


def expect_backend(expected_identity):
    """
    Return decorators that skips all updates acquired from
    backends with identity different from specified one.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, context: Context):
            if context.backend.get_identity() != expected_identity:
                return SKIPPED
            return await func(message, context)

        return wrapper

    return decorator


async def _get_user_statuses_vk(backend, chat_id, user_id):
    members_response = await backend.request(
        "messages.getConversationMembers",
        {"peer_id": chat_id, "fields": ""},
    )

    for member in members_response["items"]:
        if member["member_id"] == user_id:
            statuses = []

            if member.get("is_owner"):
                statuses.append("admin")
                statuses.append("owner")
            elif member.get("is_admin"):
                statuses.append("admin")

            return statuses

    return []


async def _get_user_statuses_tg(backend, chat_id, user_id):
    chat_administrators = await backend.request(
        "getChatAdministrators",
        {"chat_id": chat_id},
    )

    for administrator in chat_administrators:
        if administrator["user"]["id"] == user_id:
            statuses = []

            if administrator["status"] == "creator":
                statuses.extend(["admin", "owner"])
            elif administrator["status"] == "administrator":
                statuses.append("admin")

            return statuses

    return []


async def _get_user_statuses(backend: Backend, chat_id, user_id):
    if backend.get_identity() == "vk":
        return await _get_user_statuses_vk(backend, chat_id, user_id)

    if backend.get_identity() == "tg":
        return await _get_user_statuses_tg(backend, chat_id, user_id)

    raise NotImplementedError()


def _expect_sender_status(func, expected_status):
    @expect_recipient_kind(RecipientKind.GROUP_CHAT)
    @wraps(func)
    async def wrapper(message: Message, context: Context):
        sender_statuses = await _get_user_statuses(
            context.backend,
            message.recipient_id,
            message.sender_id,
        )

        if expected_status not in sender_statuses:
            return SKIPPED

        return await func(message, context)

    return wrapper


def expect_sender_is_admin():
    """
    Return decorators that skips all messages that were
    send by non-admin users (we treat owners as admins).
    """

    def decorator(func):
        return _expect_sender_status(func, "admin")

    return decorator


def expect_sender_is_owner():
    """
    Return decorators that skips all messages that were
    send by non-owner users.
    """

    def decorator(func):
        return _expect_sender_status(func, "owner")

    return decorator
