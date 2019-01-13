"""
Manager, environment and utils for interacting with Telegram.

Example "configuration.json" for TGManager ("tg_proxy" is optional):

.. code-block:: json

    {
        "tg_token": "API TOKEN",
        "tg_proxy": "http://address_of_prox:port"
    }

Example of initializating TGManager:

.. code-block:: python

    manager2 = TGManager(
        load_value("tg_token", "configuration.json"),
        load_value("tg_proxy", "configuration.json"),
    )

.. note::
    - Attachmnet type "document" is replaced with "doc" inside of engine.
    - Files and photos can't be uploaded without "send_message" or "replay".

"""

from .manager import TGManager, TGResponse
from .environment import TGEnvironment
