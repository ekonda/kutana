"""Utility functions for different purposes."""

import importlib.util
import json
import os
from os.path import dirname, isdir, join
import re

from kutana.plugin import Plugin
from kutana.logger import logger


def get_path(root, path):
    """
    Shortcut for ``join(dirname(root), path)``.

    :param root: root path
    :param path: path to file or folder
    :rtype: path to file or folder relative to root
    """

    return join(dirname(root), path)


def load_value(key, path):
    """
    Load value for key from json object in file in specified path.

    :param key: key
    :param path: path to json file
    :rtype: value for key from json object
    """

    with open(path, "r") as fh:
        config = json.load(fh)

    return config.get(key)


def import_module(name, path):
    """
    Import module from specified path with specified name.

    :param name: module's name
    :param path: path to module's file
    :rtype: imported module
    """

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def load_plugin(path, plugins_list=None, verbose=False):
    """
    Load plugin from specified path. If plugins_list is specified,
    loaded plugin will be added to this list.

    :param path: path to plugin's file
    :param plugins_list: list to add loaded plugin to (optional)
    :rtype: loaded module or None if no plugin found
    """

    module = import_module(path, path)

    if hasattr(module, "plugin") and isinstance(module.plugin, Plugin):
        if plugins_list is not None:
            plugins_list.append(module.plugin)

        logger.info("Loaded plugin \"%s\"", path)

        return module.plugin

    if verbose:  # pragma: no cover
        logger.warning("No plugin found in \"%s\"", path)

    return None


def load_plugins(folder):
    """
    Import all plugins from target folder recursively.

    :param folder: path to target folder
    :rtype: list of loaded plugins
    """

    plugins_list = []

    for name in os.listdir(folder):
        path = join(folder, name)

        if isdir(path):
            plugins_list += load_plugins(path)

        elif re.match(r"^[^_].*\.py$", name):
            load_plugin(path, plugins_list)

    return plugins_list
