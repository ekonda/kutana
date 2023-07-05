import os

from kutana.helpers import (
    get_path,
    get_random_string,
    make_hash,
    pick,
    pick_by,
    uniq_by,
)


def test_get_path():
    path = os.path.join(os.path.dirname(__file__), "bruh")
    assert get_path(__file__, "bruh") == path


def test_get_random_string():
    assert get_random_string(4) != get_random_string(4)
    assert len(get_random_string(4)) == 4


def test_make_hash():
    assert make_hash({"a": 1}) == make_hash({"a": 1})
    assert make_hash({"a": 1}) != make_hash({"a": 2})

    assert make_hash({"a": 1, "b": 2}) == make_hash({"a": 1, "b": 2})
    assert make_hash({"a": 1, "b": 2}) != make_hash({"a": 2, "b": 1})

    def make_complex_object():
        return {
            "a": {
                "b": [
                    1,
                    {"c": 2},
                    {3, "f", 4},
                ],
            },
        }

    hashes = []
    for _ in range(6):
        hashes.append(make_hash(make_complex_object()))

    assert len(set(hashes)) == 1


def test_pick():
    assert pick({"a": 1, "b": 2}, ["a", "b", "b", "b"]) == {"a": 1, "b": 2}
    assert pick({"a": 1, "b": 2}, ["a", "b"]) == {"a": 1, "b": 2}
    assert pick({"a": 1, "b": 2}, ["a"]) == {"a": 1}
    assert pick({"a": 1, "b": 2}, ["b"]) == {"b": 2}
    assert pick({"a": 1, "b": 2}, []) == {}


def test_pick_by():
    assert pick_by({"a": 1, "b": "", "c": 3}) == {"a": 1, "c": 3}
    assert pick_by({"a": 1, "b": "", "c": 3}, lambda k, v: k == "b" or v == 3) == {
        "b": "",
        "c": 3,
    }
    assert pick_by({"a": 1, "b": 2}, lambda *_: False) == {}


def test_uniq_by():
    assert uniq_by([1, 2, 3, 1, 2, 3]) == [1, 2, 3]
    assert uniq_by([1, 2, 3, 4, 5], lambda v: v % 2) == [5, 4]
    assert uniq_by([1, 2, 3, 4, 5, 6], lambda v: v % 2) == [5, 6]
