import asyncio
from asynctest import patch
import kutana.backends
from kutana.backends import Vkontakte, Telegram
from kutana.backends.vkontakte.backend import VKRequest


def test_backend_identities():
    identities = set()

    for backend_name in kutana.backends.__all__:
        backend_class = getattr(kutana.backends, backend_name)
        identity = backend_class.get_identity()
        identities.add(identity)

    assert identities

    for i1 in identities:
        for i2 in identities:
            if i1 == i2:
                continue
            assert not i1.endswith(i2)


@patch("kutana.backends.Vkontakte._request")
def test_vk_backend_api(mock):
    async def test():
        fut = VKRequest("", "")
        fut.set_result("OK")
        mock.return_value = fut

        vk = Vkontakte("token")

        resp = await vk.request("method", arg1="val1")
        assert resp == "OK"
        mock.assert_awaited_with("method", {"arg1": "val1"}, None)

        resp = await vk.send_message("user1", "msg", arg1="val1", random_id="1")
        assert resp == "OK"
        mock.assert_awaited_with(
            "messages.send", {
                "peer_id": "user1",
                "message": "msg",
                "arg1": "val1",
                "random_id": "1"
            },
        )

    asyncio.get_event_loop().run_until_complete(test())


@patch("kutana.backends.Telegram._request")
def test_tg_backend_api(mock):
    async def test():
        mock.return_value = "OK"

        tg = Telegram("token")
        tg.api_messages_lock = asyncio.Lock()

        resp = await tg.request("method", arg1="val1")
        assert resp == "OK"
        mock.assert_awaited_with("method", {"arg1": "val1"})

        resp = await tg.send_message("user1", "msg", arg1="val1")
        assert resp == ["OK"]
        mock.assert_awaited_with(
            "sendMessage", {"chat_id": "user1", "text": "msg", "arg1": "val1"},
        )

    asyncio.get_event_loop().run_until_complete(test())
