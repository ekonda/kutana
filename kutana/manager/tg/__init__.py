"""
Manager, environment and utils for interacting with Telegram.

Proxy should be in format "http://address_of_prox:port".

Example of initializating TGManager:

.. code-block:: python

    manager2 = TGManager(
        tg_token,
        proxy=tg_proxy,
    )

.. note::
    - Attachmnet type "document" is replaced with "doc" inside of application.
    - Files and photos can't be uploaded without "send_message" or "replay".

"""

from .manager import TGManager, TGResponse
from .environment import TGEnvironment
