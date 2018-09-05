Executor
========

Description
^^^^^^^^^^^

This class collects coroutines for updates processing and calls
them with the appropriate data. These coroutines receive the update
itself and the dictionary-like environment with data that could be
written there by previous and read by next coroutine calls. You can
register these callbacks with executor's :func:`subscribe`
as method or decorator. Environment has "ctrl_type" set to the type of
update's controller (VKontakte, Telegram, etc.).

.. code-block:: python

  @kutana.executor.subscribe()
  async def prc(update, eenv):
    # eenv stands for "executor's environment"
    await eenv.reply("Ого, эхо!")

Same as

.. code-block:: python

  async def prc(update, eenv):
    await env.reply("Ого, эхо!")

  kutana.executor.subscribe(prc)

All coroutine callbacks will be called in order they were added until
one of the coroutines returns **"DONE"** or none coroutines left.

You can register callbacks on exceptions in normal callbacks like that.
Exception accesible from eenv.exception in error callbacks.

.. code-block:: python

  async def prc(update, eenv):
    await env.reply("Error happened c:")

  kutana.executor.subscribe(prc, error=True)

.. note::
  You can't and shouldn't create or use your own executors. It's just
  convenient collector and executor of callbacks.
