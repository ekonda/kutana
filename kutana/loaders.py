import importlib
import importlib.util
import logging
import os
import pkgutil
import sys

from .plugin import Plugin


def _validate_plugins(plugins, package):
    for plugin in plugins:
        if not isinstance(plugin, Plugin):
            raise ValueError(
                f'Package "{package}" exported {plugin}, which is not an instance of Plugin'
            )

    return plugins


def _extract_plugins(package):
    if hasattr(package, "plugin"):
        logging.info('Loaded 1 plugin from "%s" package', package.__name__)
        return _validate_plugins([package.plugin], package.__name__)

    if hasattr(package, "plugins"):
        logging.info(
            'Loaded %d plugin(s) from "%s" package',
            len(package.plugins),
            package.__name__,
        )
        return _validate_plugins(package.plugins, package.__name__)

    logging.debug('No plugins found in "%s" package', package.__name__)
    return []


def _load_package(path):
    # Acquire finder for provided folder (if provided path is file)
    # or folder's parent (if provided path is folder)
    if os.path.isdir(path):
        parent_path = os.path.join(path, "..")
    else:
        parent_path = os.path.dirname(path)

    finder = pkgutil.get_importer(parent_path)
    if finder is None:
        raise ValueError(f'Failed to get importer from path "{parent_path}"')

    # Extract module name
    _, package_name = os.path.split(path)
    package_name = "".join(package_name.rsplit(".py", 1))

    # Import module using extracted name
    spec = finder.find_spec(package_name)
    if spec is None or spec.loader is None:
        raise ValueError(
            f'Failed to get spec for "{package_name}" (or spec has no loader)'
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module
    spec.loader.exec_module(module)

    # Return imported module
    return module


def load_plugins_from_module(module):
    return _extract_plugins(module)


def load_plugins_from_path(path):
    """
    Return list of plugins loaded from specified path. Modules are
    loaded recursively, packages are loaded non-recursively. Packages
    are detected using "__init__.py" file. Path itself can be package.
    Only plugins in module-level variables "plugin" or "plugins" are
    loaded.

    :param path: path to target folder
    :returns: list of loaded plugins
    """

    entries = os.listdir(path)

    if "__init__.py" in entries:
        return _extract_plugins(_load_package(path))

    plugins = []

    for entry in entries:
        entry_path = os.path.join(path, entry)

        if entry.startswith("__"):
            continue

        if os.path.isdir(entry_path):
            plugins.extend(load_plugins_from_path(entry_path))
        elif entry_path.endswith(".py"):
            plugins.extend(_extract_plugins(_load_package(entry_path)))

    return plugins
