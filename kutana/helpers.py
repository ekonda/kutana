import os.path


def get_path(root, path):
    """
    Shortcut for ``os.path.join(os.path.dirname(root), path)``.

    :param root: root path
    :param path: path to file or folder
    :returns: path to file or folder relative to root
    """

    return os.path.join(os.path.dirname(root), path)
