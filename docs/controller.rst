Controller
==========

Description
^^^^^^^^^^^

Controllers are responsible for receiving updates and sending responses.
Often adding new source (like vk.com) requires creation of two things:
controller and normalizer.

- Controller just exchanges messages, oversees over this exchange and
  provides means to interact with service to callbacks throught environment.
- Normalizer turns updates from raw data to instances of classes
  :class:`.Message` and :class:`.Attachment` if possible. These objects are
  then passed to plugins. They should only create instances of messages
  without editing environment.

These files are placed in folders "kutana/controllers" and
"kutana/plugins/converters".

Custom controller
^^^^^^^^^^^^^^^^^

You can simply fill required methods from :class:`kutana.BasicController`.
Use :class:`.DumpingController` as example and it's files in folders
"controllers" and "converters" with its names.

.. autoclass:: kutana.BasicController
    :members:

.. note::
  You don't have to create your own controllers if you don't want to.
