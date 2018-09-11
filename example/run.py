from kutana import Kutana, VKController, load_plugins, \
    load_configuration


# Create engine
kutana = Kutana()

# Create VKController
controller = VKController(
    load_configuration("vk_token", "configuration.json")
)

# Add controller to engine
kutana.add_controller(
    controller
)

# Load and register plugins
kutana.executor.register_plugins(
    *load_plugins("example/plugins/")
)

# Run engine
kutana.run()
