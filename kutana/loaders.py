"""Functions for loading and extracting plugins from python files."""

import importlib.util
import os
import re

from .logger import logger
from .plugin import Plugin
from .utils import is_list_or_tuple


def import_module(name, path):
    """
    Import module from specified path with specified name.

    :param name: module's name
    :param path: path to module's file
    :returns: imported module
    """

    spec = importlib.util.spec_from_file_location(name, os.path.abspath(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def load_plugins_from_file(path, verbose=False):
    """
    Load plugins from specified path. Plugins can be in module-level
    variable "plugin" and in module-level variable "plugins" with list of
    plugins.

    :param path: path to plugin's file
    :returns: loaded module or None if no plugin found
    """

    module = import_module(path, path)

    plugins = []

    possible_plugins = []

    if hasattr(module, "plugin") and isinstance(module.plugin, Plugin):
        possible_plugins.append(module.plugin)

    if hasattr(module, "plugins") and is_list_or_tuple(module.plugins):
        possible_plugins.extend(module.plugins)

    for plugin in possible_plugins:
        if plugin and isinstance(plugin, Plugin):
            plugins.append(plugin)

    if plugins:
        count = len(plugins)

        if count == 1:
            logger.info('Loaded plugin from "%s"', path)

        else:
            logger.info('Loaded %d plugins from "%s"', count, path)

    elif verbose:  # pragma: no cover
        logger.warning("No plugins found in \"%s\"", path)

    return plugins


def load_plugins(folder):
    """
    Import all plugins from target folder recursively.

    :param folder: path to target folder
    :returns: list of loaded plugins
    """

    plugins_list = []

    for name in os.listdir(folder):
        path = os.path.join(folder, name)

        if os.path.isdir(path):
            plugins_list += load_plugins(path)

        elif re.match(r"^[^_].*\.py$", name):
            plugins_list += load_plugins_from_file(path)

    return plugins_list
