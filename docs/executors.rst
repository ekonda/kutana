Executors
=========

This class collects coroutines for updates processing and calls 
them with the appropriate data. These coroutines receive the type of 
update's controller (VKontakte, Telegram, etc.), the update itself 
and the dictionary-like environment with data that could be written 
there by previous and read by next coroutine calls. You can register 
theese callbacks with executor's :func:`subscribe` as method or decorator.

.. code-block:: python

  @kutana.executor.subscribe()
  async def prc(controller_type, update, env):
    await env.reply("Ого, эхо!")

Same as

.. code-block:: python

  async def prc(controller_type, update, env):
    await env.reply("Ого, эхо!")

  kutana.executor.subscribe(prc)

All coroutine callbacks will be called in order they were added until
one of the coroutines returns **"DONE"** or none coroutines left. 

You can register callbacks on errors like that.

.. code-block:: python

  async def prc(controller_type, update, env):
    await env.reply("Error happened c:")

  kutana.executor.subscribe(prc, error=True)