Controller
==========

Description
^^^^^^^^^^^

Controllers are responsible for receiving updates, sending responses and
turning raw update data to instances of classes :class:`.Message` and
:class:`.Attachment` if possible. These instances are then passed to plugins.

Custom controller
^^^^^^^^^^^^^^^^^

You can simply fill required methods from :class:`kutana.BasicController`.
Use :class:`.DumpingController` as example and it's files in folders
"controllers" and "converters" with its names.

.. autoclass:: kutana.BasicController
    :members:

.. note::
  You don't have to create your own controllers if you don't want to.
