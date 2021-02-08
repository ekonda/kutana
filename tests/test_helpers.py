import os
from kutana.helpers import get_path, get_random_string, pick, uniq_by


def test_get_random_string():
    assert len(get_random_string(4)) == 4


def test_get_path():
    path = os.path.join(os.path.dirname(__file__), "bruh")
    assert get_path(__file__, "bruh") == path


def test_pick():
    assert pick({'a': 1, 'b': 2}, ['a', 'b', 'b', 'b'])  == {'a': 1, 'b': 2}
    assert pick({'a': 1, 'b': 2}, ['a', 'b'])  == {'a': 1, 'b': 2}
    assert pick({'a': 1, 'b': 2}, ['a'])  == {'a': 1}
    assert pick({'a': 1, 'b': 2}, ['b'])  == {'b': 2}
    assert pick({'a': 1, 'b': 2}, [])  == {}


def test_uniq_by():
    assert uniq_by([1, 2, 3, 1, 2, 3]) == [1, 2, 3]
    assert uniq_by([1, 2, 3, 4, 5], lambda v: v % 2) == [5, 4]
    assert uniq_by([1, 2, 3, 4, 5, 6], lambda v: v % 2) == [5, 6]
