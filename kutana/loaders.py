import importlib.util
import os
import re

from .i18n import load_translations
from .logger import logger
from .plugin import Plugin


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
    variable "plugin" and in module-level variable "plugins" (with list of
    plugins).

    :param path: path to file with module
    :returns: loaded module or None if no plugin found
    """

    mod = import_module(path, path)

    plugins = []

    for pl in [getattr(mod, "plugin", None), *getattr(mod, "plugins", ())]:
        if isinstance(pl, Plugin):
            plugins.append(pl)

    if len(plugins) > 1:
        logger.info('Loaded %d plugins from "%s"', len(plugins), path)
    elif len(plugins) == 1:
        logger.info('Loaded plugin from "%s"', path)
    elif verbose:
        logger.warning('No plugins found in "%s"', path)

    return plugins


def load_plugins(folder, verbose=False):
    """
    Import all plugins from target folder recursively. This
    also loads translations from "i18n" subfolders.

    :param folder: path to target folder
    :returns: list of loaded plugins
    """

    load_translations(os.path.join(folder, "i18n"))

    plugins_list = []

    for name in os.listdir(folder):
        path = os.path.join(folder, name)

        if os.path.isdir(path) and name != "i18n":
            plugins_list += load_plugins(path, verbose=verbose)

        elif re.match(r"^[^_].*\.py$", name):
            plugins_list += load_plugins_from_file(path, verbose=verbose)

    return plugins_list
