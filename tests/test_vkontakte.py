import aiohttp
import asyncio
import pytest
from asynctest import CoroutineMock, patch
from kutana import Kutana, Plugin, RequestException, Attachment
from kutana.backends import Vkontakte
from kutana.backends.vkontakte import VKRequest, NAIVE_CACHE
from test_vkontakte_data import MESSAGES, ATTACHMENTS


def test_no_token():
    with pytest.raises(ValueError):
        Vkontakte("")


@patch('aiohttp.ClientSession.post')
def test_raw_request(mock_post):
    mock_post.return_value.__aenter__.return_value.json = CoroutineMock(
        side_effect=[{"response": 1}, {"error": 1}]
    )

    async def test():
        vkontakte = Vkontakte(token="token", session=aiohttp.ClientSession())

        assert await vkontakte.raw_request("method1", {"arg": "val1"}) == 1

        with pytest.raises(RequestException):
            await vkontakte.raw_request("method2", {"arg": "val2"})

    asyncio.get_event_loop().run_until_complete(test())


@patch('kutana.backends.Vkontakte.raw_request')
def test_execute_loop_perform_execute(mock_raw_request):
    mock_raw_request.side_effect = [(1,), (1, False), (1, 2)]

    async def test():
        vkontakte = Vkontakte(token="token", session=aiohttp.ClientSession())

        tasks = [VKRequest("m1", {}), VKRequest("m2", {})]

        await vkontakte._execute_loop_perform_execute("code", tasks)

        assert tasks[0].done()
        assert tasks[1].done()
        assert tasks[0].result() == 1
        with pytest.raises(RequestException):
            assert tasks[1].result()

        tasks = [VKRequest("m1", {}), VKRequest("m2", {})]

        await vkontakte._execute_loop_perform_execute("code", tasks)

        assert tasks[0].done()
        assert tasks[1].done()
        assert tasks[0].result() == 1
        with pytest.raises(RequestException):
            assert tasks[1].result()

        tasks = [VKRequest("m1", {}), VKRequest("m2", {})]

        tasks[1].set_exception(asyncio.CancelledError)

        await vkontakte._execute_loop_perform_execute("code", tasks)

        assert tasks[0].done()
        assert tasks[1].done()
        assert tasks[0].result() == 1
        with pytest.raises(asyncio.CancelledError):
            assert tasks[1].result()

    asyncio.get_event_loop().run_until_complete(test())


@patch('kutana.backends.Vkontakte.request')
def test_resolve_screen_name(mock_request):
    data = {
        "type": "user",
        "object_id": 1
    }

    mock_request.side_effect = [data, data]

    async def test():
        vkontakte = Vkontakte(token="token", session=aiohttp.ClientSession())

        assert await vkontakte._resolve_screen_name("durov") == data
        assert await vkontakte._resolve_screen_name("durov") == data

        NAIVE_CACHE.update({i: None for i in range(500_000)})

        assert await vkontakte._resolve_screen_name("krukov") == data

        assert len(NAIVE_CACHE) == 1
        assert next(mock_request.side_effect, None) is None

    asyncio.get_event_loop().run_until_complete(test())


@patch('aiohttp.ClientSession.post')
def test_perform_updates_request(mock_post):
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
        vkontakte = Vkontakte(token="token", session=aiohttp.ClientSession())

        vkontakte.longpoll_data = {
            "ts": "ts",
            "key": "key",
            "server": "server",
        }

        await vkontakte.perform_updates_request(None)

        with pytest.raises(asyncio.CancelledError):
            await vkontakte.perform_updates_request(None)

        await vkontakte.perform_updates_request(None)

    asyncio.get_event_loop().run_until_complete(test())


@patch('aiohttp.ClientSession.post')
def test_upload_file_to_vk(mock_post):
    mock_post.return_value.__aenter__.return_value.json = CoroutineMock(
        side_effect=[{"r": "ok"}]
    )

    async def test():
        vkontakte = Vkontakte(token="token", session=aiohttp.ClientSession())
        result = await vkontakte._upload_file_to_vk("url", {"file": "file"})
        assert result == {"r": "ok"}

    asyncio.get_event_loop().run_until_complete(test())


def test_upload_attachment():
    class _Vkontakte(Vkontakte):
        async def request(self, method, kwargs):
            if method == "photos.getMessagesUploadServer":
                return {"upload_url": "upload_url_photo"}

            if method == "docs.getMessagesUploadServer":
                return {"upload_url": "upload_url_" + kwargs["type"]}

            if method == "docs.getWallUploadServer":
                return {"upload_url": "upload_url_" + kwargs["type"]}

            if method == "photos.saveMessagesPhoto":
                if kwargs["data"] == "photo":
                    return [ATTACHMENTS["image"]["photo"]]

            if method == "docs.save":
                if kwargs["data"] == "doc":
                    return ATTACHMENTS["doc"]

                if kwargs["data"] == "graffiti":
                    return ATTACHMENTS["graffiti"]

                if kwargs["data"] == "audio_message":
                    return ATTACHMENTS["voice"]

            print(method, kwargs)

        async def _upload_file_to_vk(self, url, data):
            if url == "upload_url_photo":
                return {"data": "photo"}

            if url == "upload_url_doc":
                return {"data": "doc"}

            if url == "upload_url_graffiti":
                return {"data": "graffiti"}

            if url == "upload_url_audio_message":
                return {"data": "audio_message"}

            print(url, data)

            raise RuntimeError("Unknown url")

    vkontakte = _Vkontakte(token="token")

    async def test():
        attachment = Attachment.new(b"content")
        image = await vkontakte._upload_attachment(attachment, peer_id=123)

        assert image.type == "image"
        assert image.id is not None
        assert image.file is None

        attachment = Attachment.new(b"content", type="doc")
        doc = await vkontakte._upload_attachment(attachment, peer_id=123)

        assert doc.type == "doc"
        assert doc.id is not None
        assert doc.file is None

        attachment = Attachment.new(b"content", type="voice")
        voice = await vkontakte._upload_attachment(attachment, peer_id=123)

        assert voice.type == "voice"
        assert voice.id is not None
        assert voice.file is None

        attachment = Attachment.new(b"content", type="graffiti")
        voice = await vkontakte._upload_attachment(attachment, peer_id=123)

        assert voice.type == "graffiti"
        assert voice.id == "graffiti87641997_497831521"
        assert voice.file is None

        attachment = Attachment.new(b"content", type="video")
        with pytest.raises(ValueError):
            await vkontakte._upload_attachment(attachment, peer_id=123)

    asyncio.get_event_loop().run_until_complete(test())


@patch('aiohttp.ClientSession.get')
def test_attachments(mock_get):
    mock_read = CoroutineMock(
        side_effect=["content"] * (len(ATTACHMENTS) - 2)
    )

    mock_get.return_value.__aenter__.return_value.read = mock_read

    async def test():
        vkontakte = Vkontakte(token="token", session=aiohttp.ClientSession())

        for k, v in ATTACHMENTS.items():
            attachment = vkontakte._make_attachment(v)

            if k == "graffiti":
                assert attachment.file is None
                continue

            assert attachment.type == k
            assert attachment.file is None

            if k in ("video", "graffiti"):
                continue

            assert await attachment.get_file() == "content"

        assert next(mock_read.side_effect, None) is None

    asyncio.get_event_loop().run_until_complete(test())


def test_perform_send_exception():
    vkontakte = Vkontakte(token="token")

    attachment = vkontakte._make_attachment(ATTACHMENTS["image"])
    attachment = attachment._replace(id=None)

    with pytest.raises(ValueError):
        asyncio.get_event_loop().run_until_complete(
            vkontakte.perform_send(1, "text", attachment, {})
        )


def test_perform_send_string():
    vkontakte = Vkontakte(token="token")

    async def req(method, kwargs):
        assert method == "messages.send"
        assert kwargs["attachment"] == "hey,hoy"
        return 1
    vkontakte.request = req

    result = asyncio.get_event_loop().run_until_complete(
        vkontakte.perform_send(1, "text", ("hey", "hoy"), {})
    )

    assert result == 1


def test_perform_send_sticker():
    vkontakte = Vkontakte(token="token")

    async def req(method, kwargs):
        assert method == "messages.send"
        assert kwargs["attachment"] == ""
        assert kwargs["sticker_id"] == "123"
        return 1
    vkontakte.request = req

    sticker_attachment = Attachment.existing("123", "sticker")

    result = asyncio.get_event_loop().run_until_complete(
        vkontakte.perform_send(1, "text", sticker_attachment, {})
    )

    assert result == 1


def test_perform_send_new():
    vkontakte = Vkontakte(token="token")

    async def _upl_att(attachment, peer_id):
        return attachment._replace(id=1, raw={"ok": "ok"})
    vkontakte._upload_attachment = _upl_att

    async def req(method, kwargs):
        assert method == "messages.send"
        assert kwargs["attachment"] == "1"
        return 1
    vkontakte.request = req

    attachment = Attachment.new(b"content", "image")

    result = asyncio.get_event_loop().run_until_complete(
        vkontakte.perform_send(1, "text", attachment, {})
    )

    assert result == 1


def test_perform_api_call():
    vkontakte = Vkontakte(token="token")

    async def req(method, kwargs):
        assert method == "method"
        assert kwargs["arg"] == "val"
        return 1
    vkontakte.request = req

    result = asyncio.get_event_loop().run_until_complete(
        vkontakte.perform_api_call("method", {"arg": "val"})
    )

    assert result == 1


@patch('aiohttp.ClientSession.post')
def test_happy_path(mock_post):
    group_change_settings_update = {
        "type": "group_change_settings",
        "object": {
            "changes": {
                'screen_name': {'old_value': '', 'new_value': 'sdffff23f23'},
                'title': {'old_value': 'Спасибо', 'new_value': 'Спасибо 2'}
            }
        }
    }

    raw_updates = [
        {},
        {"type": "present"},
        group_change_settings_update,
        MESSAGES["not_message"],
        MESSAGES["message"],
        MESSAGES[".echo"],
        MESSAGES[".echo chat"],
        MESSAGES[".echo wa"],
    ]

    answers = []
    updated_longpoll = []

    def acquire_updates(content_type=None):
        if not raw_updates:
            return {"updates": [], "ts": "100"}
        if updated_longpoll == [1]:
            return {"failed": 3}
        return {"updates": [raw_updates.pop(0)], "ts": "0"}

    mock_post.return_value.__aenter__.return_value.json = CoroutineMock(
        side_effect=acquire_updates
    )

    class _Vkontakte(Vkontakte):
        async def raw_request(self, method, kwargs=None):
            if kwargs is None:
                kwargs = {}

            if method == "groups.setLongPollSettings":
                return 1

            if method == "groups.getById":
                return [{"id": 1, "name": "group", "screen_name": "grp"}]

            if method == "groups.getLongPollServer":
                updated_longpoll.append(1)
                return {"server": "s", "key": "k", "ts": "1"}

            if method == "execute":
                answers.extend(kwargs["code"].split("API.")[1:])
                return [1] * kwargs["code"].count("API.")

            print(method, kwargs)

    app = Kutana()

    vkontakte = _Vkontakte(token="token")

    app.add_backend(vkontakte)

    echo_plugin = Plugin("echo")

    @echo_plugin.on_commands(["echo", "ec"])
    async def _(message, ctx):
        await ctx.reply(message.text, attachments=message.attachments)

    app.add_plugin(echo_plugin)

    app.get_loop().call_later(
        delay=vkontakte.api_request_pause * 4,
        callback=app.stop,
    )

    app.run()

    assert vkontakte.group_name == "Спасибо 2"
    assert vkontakte.group_screen_name == "sdffff23f23"

    assert len(updated_longpoll) == 2

    answers.sort()
    assert len(answers) == 3
    assert '{"message": ".echo chat [michaelkrukov|Михаил]",' in answers[0]
    assert '{"message": ".echo wa",' in answers[1]
    assert '"attachment": ""' not in answers[1]
    assert '{"message": ".echo",' in answers[2]
