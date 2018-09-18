Kutana
======

Description
^^^^^^^^^^^

Kutana is an object that runs everything. You should populate kutana
instance with controllers, plugins and executor callbacks in order
to create you engine..

.. code-block:: python

    from kutana import Kutana, VKController
    from plugins import my_plugin

    kutana = Kutana()

    kutana.add_controller(VKController(token="token"), "vkcontr)

    kutana.executor.register_plugins(my_plugin)

    kutana.run()

Storage
^^^^^^^

In order to pass some global information to plugins, you can use special
field "storage". Plugins can access this field in on_startup with
"kutana.storage". All added controllers are added to storage["controllers"]
dictionary with specified in :func:`kutana.kutana.Kutana.add_controller`
unique name as key.
