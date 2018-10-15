from kutana.logger import logger
from os.path import isdir, join, dirname
import importlib.util
import json
import os
import re


def get_path(rootpath, wantedpath):
    """Return path to wantedpath relative to rootpath."""

    return join(
        dirname(rootpath),
        wantedpath
    )


def load_configuration(target, path):
    """Load specified in target key from json file in specified path."""

    with open(path, "r") as fh:
        config = json.load(fh)

    return config.get(target)


def import_module(name, path):
    """Import module from specified path with specified name.
    Return imported module.
    """

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def load_plugin(path, plugins_list=None):
    """Load plugin from specified path. If plugins_list is specified,
    loaded plugin will be added to this lsit.
    Return loaded module or None if no plugin found.
    """

    module = import_module(path, path)

    if hasattr(module, "plugin"):
        plugins_list.append(module.plugin)

        logger.info("Loaded plugin \"{}\"".format(path))

        return module.plugin

    logger.warning("No plugin found in \"{}\"".format(path))

    return None


def load_plugins(folder):
    """Import all plugins from target folder recursively."""

    plugins_list = []

    for name in os.listdir(folder):
        path = join(folder, name)

        if isdir(path):
            plugins_list += load_plugins(path)

            continue

        if not re.match(r"^[^_].*\.py$", name):
            continue

        load_plugin(path, plugins_list)

    return plugins_list
