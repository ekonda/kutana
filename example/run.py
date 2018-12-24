from kutana import Kutana, VKManager, load_plugins, \
    load_configuration, TGManager

if __name__ == "__main__":
    # Create engine
    kutana = Kutana()

    # Create VKManager
    manager1 = VKManager(
        load_configuration("vk_token", "configuration.json")
    )

    manager2 = TGManager(
        load_configuration("tg_token", "configuration.json"),
        load_configuration("tg_proxy", "configuration.json"),
    )

    # Add manager to engine
    kutana.add_manager(
        manager1
    )

    kutana.add_manager(
        manager2
    )

    # Load and register plugins
    kutana.executor.register_plugins(
        load_plugins("plugins/")
    )

    # Run engine
    kutana.run()
