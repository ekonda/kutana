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


def import_plugin(name, path):
    """Import plugin from specified path with specified name.
    Return imported plugin or None if not plugin found.
    """

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "plugin"):
        return module.plugin

    return None

def load_plugins(folder):
    """Import all plugins from target folder recursively."""

    found_plugins = []

    for name in os.listdir(folder):
        path = join(folder, name)

        if isdir(path):
            found_plugins += load_plugins(path)

            continue

        if not re.match(r"^[^_].*\.py$", name):
            continue

        plugin = import_plugin(path, path)

        if plugin:
            found_plugins.append(plugin)

            logger.info("Loaded plugin \"{}\"".format(path))

        else:
            logger.warning("No plugin found in \"{}\"".format(path))

    return found_plugins
