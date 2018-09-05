Controllers
===========

Controllers are responsible for receiving updates and sending responses. 
Often adding new source (like vk.com) requires creation of three things: 
controller, environment and normalizer. 

- Controller just exchanges messages and oversees over this exhange.
- Environment provides convinient methods for performing different 
  operations like sending messages and uploading files.
- Normalizer turns updates from raw data to instances of classes :class:`.Message` 
  and :class:`.Attachment` if possible. Theese objects are then passed to plugins.

Theese files are placed in folders /environments, /controllers and /plguins/norm.

Custom controller
*****************

You can simply fill required methods from :class:`.BasicController`. 
Use :class:`.DumpingController` as example and it's files in folders
`/environments`, `/controllers` and `/plguins/norm` with similar names.

.. autoclass:: kutana.BasicController
    :members:

If you need to transfer some data or methods to callbacks 
(plugin's callbacks too) - it is recommended to use the environment 
dictionaries. An example of this can be seen in `environments/vk.py`.