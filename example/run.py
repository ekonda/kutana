from kutana import Kutana, VKManager, load_plugins, load_value


if __name__ == "__main__":
    # Create application
    app = Kutana()

    # Create VKManager
    manager = VKManager(
        load_value(
            "vk_token",
            "configuration.json"
        )
    )

    # Add manager to engine
    app.add_manager(
        manager
    )

    # Load and register plugins
    app.register_plugins(
        load_plugins("plugins/")
    )

    # Run application
    app.run()
