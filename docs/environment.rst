.. _environment:

Environment
===========

Environment is an dictionary (:class:`.objdict`) that has everything set by
controller or previous callbacks. Every plugin copies current executor's
environment ("eenv") to plugin's environment ("env"). That means "env" will
be destroyed after plugin done processing.

You can access executor's environment from plugin's environment
simply with "env.eenv". Changes in "eenv" will persist until update
is done being processing.


General fields
^^^^^^^^^^^^^^

This list contains frequently used fields often found inside of
executor's environment (eenv) with any controllers.

- **convert_to_message**

  This field contains controller's `convert_to_message` method
  for convenience and for converting updates to messages inside
  of plugins.

- **_cached_message**

  This field contains cached :class:`.Message` that passed to plugins.
  If you override this value, every subsequent plugin will use
  :class:`.Message` you provided. If "_cached_message" is None,
  plugin will use method from "eenv" `convert_to_message` provided by
  the controller.

- **reply**

  This fields is used for sending message to users. It accepts
  "message" as first argument. It also accepts optional
  argument "attachment" (can be list of :class:`.Attachment`).

  - :class:`.VKController`: also accepts "sticker_id", "payload",
    "forward_messages" and "keyboard".

Other fields
^^^^^^^^^^^^

- **request**

  This field contains coroutine for sending requests to controller's api.
  Usage: await env.request("method", arg1="", arg2="").

  - :class:`.VKController`: returns :class:`.VKResponse`

- **send_message**

  If accepts "message" and "peer_id" as first arguments. It also accepts
  optional argument "attachment" (can be list of :class:`.Attachment`).

  - :class:`.VKController`: also accepts "sticker_id", "payload",
    "forward_messages" and "keyboard".

- **upload_photo**

  This field contains coroutine for uploading photos. It accepts "file"
  as first argument. It can be bytes, file or path to file. It also accepts
  optional parameter "peer_id". You can pass uploaded photo as attachment to
  reply or send_message

- **upload_doc**

  This field contains coroutine for uploading files. It accepts "file"
  as first argument. It can be bytes, file or path to file. It also accepts
  optional parameters "peer_id" and "filename".

  - :class:`.VKController`: also accepts optional argument "doctype" that can
    be used to upload audio messages. You can pass uploaded photo as
    attachment to reply or send_message
