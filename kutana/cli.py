import os
import logging
import argparse
import yaml
from kutana import Kutana, load_plugins, logger
from kutana.i18n import load_translations, set_default_language
from kutana.backends import Vkontakte, VkontakteCallback, Telegram
from kutana.storages import MemoryStorage, MongoDBStorage, SqliteStorage


parser = argparse.ArgumentParser("kutana", description="Run kutana application instance using provided config.")
parser.add_argument(
    "--config", dest="config", type=str,
    default="config.yml", help="file with config in yaml format (default: config.yml",
)
parser.add_argument(
    "--plugins", dest="plugins", type=str,
    default="plugins", help="folder with plugins to load (default: plugins)",
)
parser.add_argument(
    "--translations", dest="translations", type=str,
    default="", help="folder with translations to load (default: none)",
)
parser.add_argument(
    "--debug", dest="debug", action="store_const",
    const=True, default=False,
    help="set logging level to debug",
)


def add_backends(app, backends):
    for backend in backends or []:
        kwargs = {k: v for k, v in backend.items() if k != "kind"}
        name = kwargs.get("name")

        if name and app.get_backend(name):
            logger.logger.warning(f"Duplicated backend name: {name}")

        if backend["kind"] == "vk" and "address" in backend:
            app.add_backend(VkontakteCallback(**kwargs))

        elif backend["kind"] == "vk":
            app.add_backend(Vkontakte(**kwargs))

        elif backend["kind"] == "tg":
            app.add_backend(Telegram(**kwargs))

        else:
            logger.logger.warning(f"Unknown backend kind: {backend['kind']}")


def add_storages(app, storages):
    for storage in storages or []:
        kwargs = {k: v for k, v in storage.items() if k not in ("kind", "name")}
        name = storage.get("name", "default")

        if name != "default" and app.get_storage(name):
            logger.logger.warning(f"Duplicated storage name: {name}")

        if storage["kind"] == "memory":
            app.set_storage(name, MemoryStorage(**kwargs))

        elif storage["kind"] == "mongodb":
            app.set_storage(name, MongoDBStorage(**kwargs))

        elif storage["kind"] == "sqlite":
            app.set_storage(name, SqliteStorage(**kwargs))

        else:
            logger.logger.warning(f"Unknown storage kind: {storage['kind']}")


def run():
    """
    This function runs kutana application using provided
    configuration and CLI options.

    Refer to its source to create more specific starter for
    your application.
    """

    # Parse provided arguments
    args = parser.parse_args()

    # Setup logger
    if args.debug:
        logger.set_logger_level(logging.DEBUG)

    # Import configuration
    if not os.path.isfile(args.config):
        logger.logger.error(f"Couldn't open confiuration file: {args.config}")
        exit(1)

    with open(args.config) as fh:
        config = yaml.safe_load(fh)

    # Create application
    app = Kutana()

    # Update configuration
    app.config.update(config)

    # Setup i18n
    set_default_language(config.get("language", "en"))
    load_translations(args.translations)

    # Add each backend from config
    add_backends(app, config.get("backends"))

    # Add each storage from config
    add_storages(app, config.get("storages"))

    # Load and register plugins from provided path
    app.add_plugins(load_plugins(args.plugins))

    # Run application
    app.run()


if __name__ == "__main__":
    run()
