import string
import random
import os.path


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
