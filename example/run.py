from kutana import Kutana, VKManager, load_plugins, \
    load_value, set_logger_level


if __name__ == "__main__":
    # Create engine
    kutana = Kutana()

    # Create VKManager
    manager = VKManager(
        load_value(
            "vk_token",
            "configuration.json"
        )
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
