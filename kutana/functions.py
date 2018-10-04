from kutana.logger import logger
from os.path import isdir, join, dirname
import importlib.util
import json
import os


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
    """Import plugin from specified path with specified name."""

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.plugin

def load_plugins(folder, verbose=True):
    """Import all plugins from target folder recursively."""

    found_plugins = []

    for name in os.listdir(folder):
        path = join(folder, name)

        if isdir(path):
            found_plugins += load_plugins(path)

            continue

        if "_" == name[:1] or ".py" != name[-3:]:
            continue

        if verbose:
            logger.info("Loading plugin \"{}\"".format(path))

        found_plugins.append(import_plugin(path, path))

    return found_plugins
