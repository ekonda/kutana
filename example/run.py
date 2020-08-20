import json
from kutana import Kutana, load_plugins
from kutana.backends import Vkontakte, VkontakteCallback, Telegram

# Import configuration
with open("config.json") as fh:
    config = json.load(fh)

# Create application
app = Kutana()

# Add backends to application
if "vk" in config:
    if "address" in config["vk"]:
        app.add_backend(VkontakteCallback(
            token=config["vk"]["token"],
            address=config["vk"]["address"]
        ))
    else:
        app.add_backend(Vkontakte(token=config["vk"]["token"]))

if "tg" in config:
    app.add_backend(Telegram(token=config["tg"]["token"]))

# Load and register plugins
app.add_plugins(load_plugins("plugins/"))

if __name__ == "__main__":
    # Run application
    app.run()
