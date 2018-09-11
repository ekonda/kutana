.. _special_updates:

Special updates
===============

Startup
^^^^^^^

When kutana starts, it sends update with some data
(ctrl_type is "kutana") to executors. Update example:

.. code-block:: python

    {
        # kutana object
        "kutana": self,

        # update type
        "update_type": "startup",

        # list of registered callbacks owners
        "registered_plugins": self.executor.registered_plugins
    }
