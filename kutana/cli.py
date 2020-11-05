import logging
import argparse
import yaml
from kutana import Kutana, load_plugins, logger
from kutana.backends import Vkontakte, VkontakteCallback, Telegram


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
        if backend["kind"] == "vk" and "address" in backend:
            app.add_backend(VkontakteCallback(
                token=backend["token"],
                address=backend["address"]
            ))

        elif backend["kind"] == "vk":
            app.add_backend(Vkontakte(token=backend["token"]))

        elif backend["kind"] == "tg":
            app.add_backend(Telegram(token=backend["token"]))

    # Load and register plugins
    app.add_plugins(load_plugins(args.plugins))

    # Run application
    app.run()
