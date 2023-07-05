from unittest.mock import AsyncMock, patch

from kutana.backends.vkontakte import VkontakteCallback


class FakeRequest:
    async def json(self):
        return {
            "type": "confirmation",
            "group_id": 1001,
        }


async def test_vkontakte_callback():
    backend = VkontakteCallback("token")

    request = FakeRequest()

    with patch(
        "kutana.backends.vkontakte.VkontakteCallback._direct_request",
        new=AsyncMock(return_value={"code": "FG34F"}),
    ):
        response = await backend._handle_request(request)

    assert response.body._value == b"FG34F"  # type: ignore
