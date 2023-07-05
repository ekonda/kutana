import pytest

from kutana.update import Attachment, AttachmentKind


async def test_get_content():
    async def getter():
        return b"file"

    attachment1 = Attachment(1, AttachmentKind.IMAGE, None, None, None, getter)
    attachment2 = Attachment(1, AttachmentKind.IMAGE, None, None, None, None)

    assert await attachment1.get_content() == b"file"

    with pytest.raises(ValueError):
        assert await attachment2.get_content()
