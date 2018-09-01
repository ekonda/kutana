from kutana import VKKutana, load_plugins

# Create engine with VK throught shortcut
kutana = VKKutana(configuration="configuration.json")

# Set your settings
kutana.settings["bot_name"] = "V"
kutana.settings["path_to_plugins"] = "example/plugins/"

# Load and register plugins
kutana.executor.register_plugins(*load_plugins(kutana.settings.path_to_plugins))

# Run engine
kutana.run()
