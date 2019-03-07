"""Utility functions for different purposes."""

from os.path import dirname, join


def sort_callbacks(callbacks):
    """
    Sort passed list of callbacks by it's first argument (priority) in
    descending order.

    :param callbacks: list of callbacks
    """

    callbacks.sort(key=lambda p: -p[0])


def is_list_or_tuple(obj):
    """
    Return True if object is list or tuple.

    :param obj: object to check
    :returns: True or False
    """

    return isinstance(obj, (list, tuple))


def get_path(root, path):
    """
    Shortcut for ``join(dirname(root), path)``.

    :param root: root path
    :param path: path to file or folder
    :returns: path to file or folder relative to root
    """

    return join(dirname(root), path)
