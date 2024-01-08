import os.path
import random
import string

import httpx


def create_httpx_async_client():
    return httpx.AsyncClient(timeout=55)


def second_arg(_, value):
    return value


def uniq_by(arr, key=None):
    if key:
        return list({key(element): element for element in arr}.values())
    else:
        return list(set(arr))


def pick(obj, keys):
    new_obj = {}
    for key in keys:
        if key in obj:
            new_obj[key] = obj[key]
    return new_obj


def pick_by(obj, predicate=None):
    predicate = predicate or second_arg
    new_obj = {}
    for key, value in obj.items():
        if predicate(key, value):
            new_obj[key] = value
    return new_obj


def chunks(iterable, length=4096):
    for i in range(0, len(iterable), length):
        yield iterable[i : i + length]


def get_random_string(length=14):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def make_hash(obj, hash_func=hash):
    """
    Return hash of provided object. This method supports hash of:
    - set, tuple, list;
    - dict;
    - other valuse already supported by "hash_func".
    """
    if isinstance(obj, (set, tuple, list)):
        return tuple(map(make_hash, obj))
    elif isinstance(obj, dict):
        return make_hash(tuple(obj.items()))
    else:
        return hash_func(obj)


def get_path(root, path):
    """
    Shortcut for ``os.path.join(os.path.dirname(root), path)``.

    :param root: root path
    :param path: path to file or folder
    :returns: path to file or folder relative to root
    """

    return os.path.join(os.path.dirname(root), path)
