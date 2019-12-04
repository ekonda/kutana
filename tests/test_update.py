import asyncio
import pytest
from kutana.update import Attachment


def test_get_file():
    def _get_file(attachment):
        return asyncio.get_event_loop().run_until_complete(
            attachment.get_file()
        )

    async def getter():
        return b"file"

    attachment1 = Attachment._existing_full(1, "", "", "", getter, {"ok": "ok"})
    attachment2 = Attachment._existing_full(1, "", "", "", None, {"ok": "ok"})
    attachment3 = attachment2._replace(file=b"filefile")

    assert _get_file(attachment1) == b"file"
    assert _get_file(attachment3) == b"filefile"

    with pytest.raises(ValueError):
        assert _get_file(attachment2)
