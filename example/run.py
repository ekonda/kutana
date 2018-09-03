from kutana import Kutana, VKController, load_plugins, load_configuration

# Create engine
kutana = Kutana()

# Add VKController to engine
kutana.add_controller(
    VKController(load_configuration("vk_token", "configuration.json"))
)

# Load and register plugins
kutana.executor.register_plugins(*load_plugins("example/plugins/"))

# Run engine
kutana.run()
