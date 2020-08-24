import sys
import asyncio
from asynctest import patch
from kutana.backends import Terminal


IS_WINDOWS = sys.platform == "win32"


@patch("builtins.print")
def test_execute_send(mock):
    async def test():
        await Terminal().execute_send(0, "msg", (), {})
        mock.assert_called_once_with(">", "msg")

    asyncio.get_event_loop().run_until_complete(test())

@patch('msvcrt.kbhit' if IS_WINDOWS else 'select.select')
@patch('sys.stdin.readline')
def test_request(mock2, mock1):
    if IS_WINDOWS:
        mock1.return_value = True
    else:
        mock1.return_value = (True, (), ())
    mock2.return_value = "msg"

    upds = []

    async def submit_update(upd):
        upds.append(upd)

    async def test():
        await Terminal().acquire_updates(submit_update)
        assert upds[0].text == "msg"

    asyncio.get_event_loop().run_until_complete(test())
