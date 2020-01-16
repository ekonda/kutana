import asyncio
from asynctest import patch
from kutana.backends import Terminal


@patch("builtins.print")
def test_perform_send(mock):
    async def test():
        await Terminal().perform_send(0, "msg", (), {})
        mock.assert_called_once_with(">", "msg")

    asyncio.get_event_loop().run_until_complete(test())

@patch('select.select')
@patch('sys.stdin.readline')
def test_request(mock2, mock1):
    mock1.return_value = (True, (), ())
    mock2.return_value = "msg"

    upds = []

    async def submit_update(upd):
        upds.append(upd)

    async def test():
        await Terminal().perform_updates_request(submit_update)
        assert upds[0].text == "msg"

    asyncio.get_event_loop().run_until_complete(test())
