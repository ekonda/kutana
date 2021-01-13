Kutana documentation
====================

.. image:: _static/kutana-logo-512.png
    :alt: Kutana
    :scale: 60%

.. note::
    We apologize in advance for errors and omissions in this documentation.
    If you can help improve the documentation correctness, we will be very
    grateful.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Overview
--------
Kutana is an engine for developing bots for social networks, messengers and
other services. Kutana heavily uses asyncio and coroutines. It supports
different backends (like vk.com, telegram.org etc.).

Refer to `example
<https://github.com/ekonda/kutana/tree/master/example/>`_ folder for
the showcase of the library abilities.

Workflow
--------

You can use kutana from CLI or from your python code. The CLI variant is
preferable, because it does many things you expect without excessive
boilerplace.

From CLI
^^^^^^^^

.. code-block:: bash

    python3 -m kutana --config example/config.yml --plugins example/plugins

    # usage: python3 -m kutana [-h] [--config CONFIG] [--plugins PLUGINS] [--debug]

    # Run kutana application instance using provided config.

    # optional arguments:
    #   -h, --help         show this help message and exit
    #   --config CONFIG    file with config in yaml format (default: config.yml
    #   --plugins PLUGINS  folder with plugins to load (default: plugins)
    #   --debug            set logging level to debug

Example configuration:

.. code-block:: yaml

    prefixes: ['.', '!', '/']
    language: ru
    backends:
    - kind: vk
        token: <token-for-vk-here>
    - kind: tg
        token: <token-for-tg-here>
    storages:
    - name: default
        kind: sqlite
        path: kutana.sqlite3

From python
^^^^^^^^^^^

Below you can find the most simple `run.py` file for kutana application,
that uses one Vkontakte account and loads plugins from folder `plugins/`.

.. code-block:: python

    from kutana import Kutana, load_plugins
    from kutana.backends import Vkontakte

    app = Kutana()
    app.add_backend(Vkontakte(token=VK_API_TOKEN))
    app.add_plugins(load_plugins("plugins/"))
    app.run()

Plugins
-------

Main functionality for your applications are provided by plugins:
they can add commands, process and preprocess messages, e.t.c.

Below your can find example of simple plugin `echo.py` (that should
be put into `plugins` folder).

.. code-block:: python

    from kutana import Plugin, t

    plugin = Plugin(name=t("Echo"), description=t("Sends your messages back (.echo)"))

    @plugin.on_commands(["echo"])
    async def __(msg, ctx):
        await ctx.reply("{}".format(ctx.body or '(/)'), attachments=msg.attachments, disable_mentions=0)

Handlers for messages receive :class:`kutana.update.Message` and
:class:`kutana.context.Context` as arguments. You can find description of
their methods for these classes in Full API.

You can find descriptions of all possible "on_*" methods for adding your
callbacks in :class:`kutana.plugin.Plugin` class.

Order of "on_*" methods
^^^^^^^^^^^^^^^^^^^^^^^
Default order of processors:

- on_messages, on_updates: 9
- on_payloads (vk): 7
- on_commands: 6
- on_attachments: 3
- on_unprocessed_messages, on_unprocessed_updates: -3
- Rest: ~0

Attachments
^^^^^^^^^^^

Interactions with backends are highly unified, because we want you to have
no problems creating plugins that will work nicely with multiple backends.

You can manage your attachments throught class :class:`kutana.update.Attachment`.
new attachments can be created using :meth:`kutana.update.Attachment.new`.

Attachments are files that can have types. If type is unique to backends -
you still can use them, but you will need to manager their uploads,
parsing, e.t.c. on your own.

Existing attachments (that already uploaded for example) can be created using
:meth:`kutana.update.Attachment.existing`. Many backends capable of forwarding
raw strings (supported by your service) while sending messages.

Available built-in attachment types:

- image
- doc
- sticker
- video
- audio
- voice

Not every backend can interact well with all the types, so you should
be careful. If you have troubling examples - create an issue in the
repository and we'll update documentation!

API Requests
^^^^^^^^^^^^

In order to perform a request to your backends, your should use
:meth:`kutana.context.Context.request` method. It accepts method that you
want to use and any keyword arguments that should be processable by your
backend. You can check what backend context belongs to by accessing it's
`backend` attribute.

Internationalization
^^^^^^^^^^^^^^^^^^^^

Kutana uses simple format for translations in form of ".yml" files,
containing list of objects describing each translated string in
following format:

.. code-block:: yaml

    - msgctx: 'New user's greeting'
      msgid: 'Hello'
      msgstr: 'Привет'

When translated string is a subject to pluralization, you must provide
list of strings intead of string in field "msgstr". Currently only
pluralization supported for following languages: "ru", "uk", "en".

Support for different languages will be implemented in the future.
Currently you add your language into inner classes of
:class:`kutana.i18n.pluralization.Pluralization`.

Translations for strings used in library and plugins are loaded from
following places (with corresponding order):

- Default translations
- <current-working-directory>/i18n/\*.yml
- <translations-directory>/\*.yml
- <plugins-directory>/i18n/\*.yml

Where "translations-directory" is directory specified in CLI arguments of the
module. You can use :meth:`kutana.i18n.load_translations` to load translations
from your desired location.

Where "plugins-directory" is any directory that was traversed in search of
plugins using CLI interface or "load_plugins" method directly.

"kutana-i18n" command can be used to collect message from sources. If your
messages is not detected, create example and post to to github issues.

-------------------------------------------------------------------------------

.. toctree::
    :maxdepth: 1
    :caption: API Reference

    Backends <src/kutana.backends>
    Plugin <src/kutana.plugin>
    Kutana <src/kutana.kutana>
    Full API <src/modules>
