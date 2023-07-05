import argparse
import logging
import os
from importlib import import_module

import yaml

from . import Kutana
from .backends import Telegram, VkontakteCallback, VkontakteLongpoll
from .loaders import load_plugins_from_module, load_plugins_from_path
from .storages import MemoryStorage, MongoDBStorage, SqliteStorage


class CuteSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def get_parser():
    parser = argparse.ArgumentParser("kutana", description="helpfull cli utility")
    subparsers = parser.add_subparsers(dest="command")

    # Project initialization
    parser_init = subparsers.add_parser("init", help="initiate kutana project")
    parser_init.add_argument(
        "path",
        type=str,
        default=None,
        help="path to folder to populate with default project config",
    )

    # Project running
    parser_run = subparsers.add_parser(
        "run",
        help="run kutana project using provided config (working directory will be changed to the one with config file)",
    )
    parser_run.add_argument(
        "path",
        type=str,
        default="config.yml",
        help="path to config of the project",
    )
    parser_run.add_argument(
        "--debug",
        dest="debug",
        default=False,
        action="store_true",
        help="set logging level to debug",
    )

    return parser


def initiate_project(args):
    project_root = args.path or "."

    if os.path.isfile(project_root):
        logging.error(f"Specified project folder is a plain file: {project_root}")
        exit(1)

    if not os.path.isdir(project_root):
        os.makedirs(project_root)

    config_file = os.path.join(project_root, "config.yml")

    if os.path.isfile(config_file):
        logging.error(f"Specified project folder already has configuration: {project_root}/config.yml")
        exit(1)

    with open(config_file, "w") as fh:
        yaml.dump({
            "backends": [],
            "plugins": ["plugins/"],
            "prefixes": [".", "!", "/"],
            "storages": [],
        }, fh, Dumper=CuteSafeDumper)


def run_project(args):  # noqa:C901
    # Load configuration
    with open(args.path) as fh:
        config = yaml.safe_load(fh)

    # Change the current working directory to one where config is
    os.chdir(os.path.dirname(args.path))

    # Change logging level if needed
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initiate application
    app = Kutana()

    # Populate configuration
    app.config.update(config)

    # Add storages
    for storage_config in config.get("storages", ()):
        storage_name = storage_config["name"]

        if storage_config["kind"] == "memory":
            storage_class = MemoryStorage
        elif storage_config["kind"] == "mongodb":
            storage_class = MongoDBStorage
        elif storage_config["kind"] == "sqlite":
            storage_class = SqliteStorage
        else:
            raise ValueError(f'Unknown storage kind: "{storage_config["kind"]}"')

        storage_kwargs = {**storage_config}
        storage_kwargs.pop("name")
        storage_kwargs.pop("kind")

        app.add_storage(storage_name, storage_class(**storage_kwargs))

    # Add backends
    for backend_config in config.get("backends", ()):
        if backend_config["kind"] == "vk-lp":
            backend_class = VkontakteLongpoll
        elif backend_config["kind"] == "vk-cb":
            backend_class = VkontakteCallback
        elif backend_config["kind"] == "tg":
            backend_class = Telegram
        else:
            raise ValueError(f'Unknown backend kind: "{backend_config["kind"]}"')

        backend_kwargs = {**backend_config}
        backend_kwargs.pop("kind")

        app.add_backend(backend_class(**backend_kwargs))

    # Add plugins
    for plugin_config in config.get("plugins", ()):
        if isinstance(plugin_config, str):
            for plugin in load_plugins_from_path(plugin_config):
                app.add_plugin(plugin)
        elif not isinstance(plugin_config, dict) or len(plugin_config) != 1:
            raise ValueError(f'Unknown plugin config format: "{plugin_config}"')
        elif plugin_config.get("path"):
            for plugin in load_plugins_from_path(plugin_config["path"]):
                app.add_plugin(plugin)
        elif plugin_config.get("module"):
            app.add_plugin(load_plugins_from_module(import_module(plugin_config["module"])))
        else:
            raise ValueError(f'Unknown plugin config kind: "{plugin_config}"')

    # Run the application
    app.run()


if __name__ == "__main__":
    args = get_parser().parse_args()

    if args.command == "init":
        initiate_project(args)
    elif args.command == "run":
        run_project(args)
