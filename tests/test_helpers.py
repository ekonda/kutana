import os
from kutana.helpers import get_path


def test_get_path():
    path = os.path.join(os.path.dirname(__file__), "bruh")
    assert get_path(__file__, "bruh") == path
