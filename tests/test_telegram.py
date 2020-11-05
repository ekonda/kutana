import aiohttp
import asyncio
import pytest
from asynctest import CoroutineMock, patch
from kutana import Kutana, Plugin, RequestException, Attachment
from kutana.backends import Telegram
from test_telegram_data import MESSAGES, ATTACHMENTS


def test_no_token():
    with pytest.raises(ValueError):
        Telegram("")


@patch('aiohttp.ClientSession.post')
def test_request(mock_post):
    mock_post.return_value.__aenter__.return_value.json = CoroutineMock(
        side_effect=[{"ok": True, "result": 1}, {"ok": False}]
    )

    async def test():
        telegram = Telegram(token="token")

        assert await telegram._request("method1", {"arg": "val1"}) == 1

        with pytest.raises(RequestException):
            await telegram._request("method2", {"arg": "val2"})

        await telegram.session.close()

    asyncio.get_event_loop().run_until_complete(test())


@patch('aiohttp.ClientSession.get')
def test_request_file_and_getter(mock_get):
    mock_get.return_value.__aenter__.return_value.read = CoroutineMock(
        side_effect=[b"content", b"content"]
    )

    async def test():
        telegram = Telegram(token="token", session=aiohttp.ClientSession())

        async def req(method, kwargs={}):
            if method == "getFile" and kwargs["file_id"] == "file_id":
                return {"file_path": "123"}
        telegram._request = req

        assert await telegram._request_file("file_id") == b"content"
        assert await telegram._make_getter("file_id")() == b"content"

    asyncio.get_event_loop().run_until_complete(test())


@patch('aiohttp.ClientSession.post')
def test_acquire_updates(mock_post):
    def make_mock(exc):
        cm = CoroutineMock()
        cm.__aenter__ = CoroutineMock(side_effect=exc)
        cm.__aexit__ = CoroutineMock()
        return cm

    mock_post.side_effect = [
        make_mock(aiohttp.ClientError()),
        make_mock(asyncio.CancelledError()),
        make_mock(Exception()),
    ]

    async def test():
        telegram = Telegram(token="token", session=aiohttp.ClientSession())

        await telegram.acquire_updates(None)

        with pytest.raises(asyncio.CancelledError):
            await telegram.acquire_updates(None)

        await telegram.acquire_updates(None)

        await telegram.session.close()

    asyncio.get_event_loop().run_until_complete(test())


def test_attachments():
    async def test():
        telegram = Telegram(token="token", session=aiohttp.ClientSession())

        async def _req_f(file_id):
            return b"content"
        telegram._request_file = _req_f

        for k, v in ATTACHMENTS.items():
            attachment = telegram._make_attachment(*v)

            assert attachment.type == k
            assert attachment.file is None

            if k == "location":
                continue

            assert await attachment.get_file() == b"content"

    asyncio.get_event_loop().run_until_complete(test())


def test_upload_attachments():
    requests = []

    async def test():
        telegram = Telegram(token="token", session=aiohttp.ClientSession())
        telegram.api_messages_lock = asyncio.Lock()

        async def req(method, kwargs):
            requests.append((method, kwargs))
        telegram._request = req

        attachment = Attachment.new(b"file")
        await telegram.execute_send(1, "", attachment, {})

        attachment = Attachment.new(b"file", type="doc")
        await telegram.execute_send(1, "", attachment, {})

        attachment = Attachment.new(b"file", type="voice")
        await telegram.execute_send(1, "", attachment, {})

        assert len(requests) == 3

        assert requests[0] == ("sendPhoto", {
            "chat_id": "1", "photo": b"file"
        })
        assert requests[1] == ("sendDocument", {
            "chat_id": '1', "document": b'file'
        })
        assert requests[2] == ("sendVoice", {
            "chat_id": '1', "voice": b'file'
        })

    asyncio.get_event_loop().run_until_complete(test())


def test_upload_attachment_unknown_type():
    async def test():
        telegram = Telegram(token="token", session=aiohttp.ClientSession())
        telegram.api_messages_lock = asyncio.Lock()

        attachment = Attachment.new(b"bruh", type="location")

        with pytest.raises(ValueError):
            await telegram.execute_send(1, "", attachment, {})

    asyncio.get_event_loop().run_until_complete(test())


def test_execute_request():
    telegram = Telegram(token="token")

    async def req(method, kwargs):
        assert method == "method"
        assert kwargs["arg"] == "val"
        return 1
    telegram._request = req

    result = asyncio.get_event_loop().run_until_complete(
        telegram.execute_request("method", {"arg": "val"})
    )

    assert result == 1


def test_happy_path():
    updates = [
        MESSAGES["not_message"],
        MESSAGES["message"],
        MESSAGES[".echo"],
        MESSAGES[".echo chat"],
        MESSAGES["/echo@bot chat"],
        MESSAGES["/echo chat"],
        MESSAGES[".echo@bot chat"],
        MESSAGES["_image"],
    ]

    answers = []

    class _Telegram(Telegram):
        async def _request(self, method, kwargs={}):
            if method == "getMe":
                return {"first_name": "te", "last_name": "st", "username": "bot"}

            if method == "getUpdates":
                if not updates:
                    return []
                return [updates.pop(0)]

            if method == "sendMessage":
                answers.append(("msg", kwargs["text"]))
                return 1

            if method == "sendPhoto":
                answers.append(("image", kwargs["photo"]))
                return 1

            print(method, kwargs)

    app = Kutana()

    telegram = _Telegram(token="token")

    app.add_backend(telegram)

    echo_plugin = Plugin("echo")

    @echo_plugin.on_commands(["echo", "ec"])
    async def __(message, ctx):
        await ctx.reply(message.text)

    @echo_plugin.on_attachments(["image"])
    async def __(message, ctx):
        await ctx.reply(message.text, attachments=message.attachments[0])

    app.add_plugin(echo_plugin)

    app.get_loop().call_later(
        delay=0.5,
        callback=app.stop,
    )

    app.run()

    answers.sort()
    assert len(answers) == 5
    assert answers[0][0] == "image"
    assert answers[1] == ("msg", ".echo")
    assert answers[2] == ("msg", ".echo chat")
    assert answers[3] == ("msg", "/echo chat")
    assert answers[4] == ("msg", "/echo chat")
