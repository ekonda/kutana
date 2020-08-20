from .extensions import VkontaktePluginExtension
from .longpoll import VkontakteLongpoll
from .callback import VkontakteCallback


Vkontakte = VkontakteLongpoll  # Alias for backward compatibility


__all__ = [
    "VkontaktePluginExtension",
    "Vkontakte", "VkontakteLongpoll",
    "VkontakteCallback",
]
