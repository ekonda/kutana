Kutana
======

Description
^^^^^^^^^^^

Kutana is an object that runs everything. You should populate kutana
instance with controllers, plugins and executor callbacks in order
to create your app.

Storage
^^^^^^^

In order to pass some global information to plugins, you can use special
field "storage". Plugins can access this field in on_startup with
"kutana.storage".
