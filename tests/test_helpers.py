import os
from kutana.helpers import get_path, get_random_string


def test_get_random_string():
    assert len(get_random_string(4)) == 4


def test_get_path():
    path = os.path.join(os.path.dirname(__file__), "bruh")
    assert get_path(__file__, "bruh") == path
