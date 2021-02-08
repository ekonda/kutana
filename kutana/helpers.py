import string
import random
import os.path


def uniq_by(arr, key=None):
    if not key:
        def key(element):
            return element
    return list({key(element): element for element in arr}.values())


def pick(obj, keys):
    new_obj = {}
    for key in keys:
        if key in obj:
            new_obj[key] = obj[key]
    return new_obj


def get_random_string(length=16):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def get_path(root, path):
    """
    Shortcut for ``os.path.join(os.path.dirname(root), path)``.

    :param root: root path
    :param path: path to file or folder
    :returns: path to file or folder relative to root
    """

    return os.path.join(os.path.dirname(root), path)


def ensure_list(value):
    if isinstance(value, (list, tuple)):
        return value
    return [value]
