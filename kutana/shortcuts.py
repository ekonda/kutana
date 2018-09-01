from kutana.kutana import Kutana
from kutana.environments.vk import create_vk_env


def VKKutana(token=None, configuration=None):
    """Shortcut for creating kutana object and applying VK environment."""

    # Create engine
    kutana = Kutana()

    # Create VK controller and environment
    kutana.apply_environment(
        create_vk_env(token=token, configuration=configuration)
    )

    return kutana
