"""
Manager, environment and utils for interacting with VKontakte.

Example "configuration.json" for VKManager:

.. code-block:: json

    {
        "vk_token": "API TOKEN",
    }

Example of initializating VKManager:

.. code-block:: python

    manager1 = VKManager(
        load_value("vk_token", "configuration.json")
    )

"""

from .manager import VKManager, VKRequest, VKResponse
from .environment import VKEnvironment
