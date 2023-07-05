import pytest

from kutana.exceptions import RequestException


def test_request_exception():
    with pytest.raises(RequestException):
        raise RequestException(None, None, None, None, None)
