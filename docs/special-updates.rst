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
        "callbacks_owners": self.executor.callbacks_owners
    }
