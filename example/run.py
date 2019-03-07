import json

from kutana import Kutana, VKManager, load_plugins


# Load configuration
with open("configuration.json") as fh:
    config = json.load(fh)


# Create application
app = Kutana()

# Add manager to application
app.add_manager(
    VKManager(config["vk_token"])
)

# Load and register plugins
app.register_plugins(
    load_plugins("plugins/")
)

if __name__ == "__main__":
    # Run application
    app.run()
