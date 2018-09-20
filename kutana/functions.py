from kutana.logger import logger
import importlib.util
import json
import os


def get_path(rootpath, wantedpath):
    """Return path to wantedpath relative to rootpath."""

    return os.path.join(
        os.path.dirname(rootpath),
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

def load_plugins(plugins_folder, verbose=True):
    """Import all plugins from target folder recursively."""

    found_plugins = []

    for pack in os.walk(plugins_folder):
        for filename in pack[2]:
            if "_" == filename[:1] or ".py" != filename[-3:]:
                continue

            path_to_module = os.path.join(pack[0], filename)

            if verbose:
                logger.info("Loading plugin \"{}\"".format(path_to_module))

            found_plugins.append(
                import_plugin(path_to_module, path_to_module)
            )

    return found_plugins
