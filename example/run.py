from kutana import Kutana, VKManager, load_plugins, \
    load_configuration, TGManager

if __name__ == "__main__":
    # Create engine
    kutana = Kutana()

    # Create VKManager
    manager = VKManager(
        load_configuration("vk_token", "configuration.json")
    )

    # Add manager to engine
    kutana.add_manager(
        manager
    )

    # Load and register plugins
    kutana.executor.register_plugins(
        load_plugins("plugins/")
    )

    # Run engine
    kutana.run()
