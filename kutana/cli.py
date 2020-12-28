import logging
import argparse
import yaml
from kutana import Kutana, load_plugins, logger
from kutana.backends import Vkontakte, VkontakteCallback, Telegram
from kutana.storages import MemoryStorage, MongoDBStorage


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
    "--debug", dest="debug", action="store_const",
    const=True, default=False,
    help="set logging level to debug",
)


def run():
    """
    This function runs kutana application using provided
    configuration and CLI options.

    Refer to its source to create more specific starter for
    your application.
    """

    args = parser.parse_args()

    if args.debug:
        logger.set_logger_level(logging.DEBUG)

    # Import configuration
    with open(args.config) as fh:
        config = yaml.safe_load(fh)

    # Create application
    app = Kutana()

    # Update configuration
    app.config.update(config)

    # Add each backend from config
    for backend in config.get("backends"):
        kwargs = {k: v for k, v in backend.items() if k != "kind"}

        if backend["kind"] == "vk" and "address" in backend:
            app.add_backend(VkontakteCallback(**kwargs))

        elif backend["kind"] == "vk":
            app.add_backend(Vkontakte(**kwargs))

        elif backend["kind"] == "tg":
            app.add_backend(Telegram(**kwargs))

        else:
            logger.logger.warning(f"Unknown backend kind: {backend['kind']}")

    # Add each storage from config
    for name, storage in config.get("storages").items():
        kwargs = {k: v for k, v in storage.items() if k != "kind"}

        if storage["kind"] == "memory":
            app.set_storage(name, MemoryStorage(**kwargs))

        elif storage["kind"] == "mongodb":
            app.set_storage(name, MongoDBStorage(**kwargs))

        else:
            logger.logger.warning(f"Unknown storage kind: {storage['kind']}")

    # Load and register plugins
    app.add_plugins(load_plugins(args.plugins))

    # Run application
    app.run()
