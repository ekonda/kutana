"""
Manager, environment and utils for interacting with VKontakte.

Example of initializating VKManager:

.. code-block:: python

    manager1 = VKManager(
        vk_token
    )

"""

from .manager import VKManager, VKRequest, VKResponse
from .environment import VKEnvironment
