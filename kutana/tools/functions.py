from kutana.logger import logger
import importlib.util
import os


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

            path_to_module = os.path.join(plugins_folder, filename)

            if verbose:
                logger.info("Loading plugin \"{}\"".format(path_to_module))

            plugin = import_plugin(path_to_module, path_to_module)

            found_plugins.append(plugin)

        for folder in pack[1]:
            found_plugins += load_plugins(os.path.join(plugins_folder, folder))

    return sorted(found_plugins, key=lambda pl: pl.order)
