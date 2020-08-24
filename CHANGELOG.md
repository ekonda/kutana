# Changelog

> Changes to public API are marked as `^`. Possible changes
> to public API are marked as `^?`.

- v4.4.0 - WIP
  - ^ Removed `Storage`, `set_state`, `group_state`, `user_state`,
      `storage`.
  - Added stripping of mentions for the telegram bot
  - Added `VkontakteCallback`; `Vkontakte` is now
      alias for `VkontakteLongpoll`
  - Updated "stream" plugin to be more adequate

- v4.3.0
  - Added router for vkontakte's chat actions + tests
  - ^ Renamed some plugin's decorators. Old decorators will
      still work but is considered deprecated. It's possible,
      that this change will be undone, or further updated. List
      of changed names:
    - `on_any_message` -> `on_messages`
    - `on_any_unprocessed_message` -> `on_unprocessed_messages`
    - `on_any_update` -> `on_updates`
    - `on_any_unprocessed_update` -> `on_unprocessed_updates`
    - `on_payload` -> `on_payloads`

- v4.2.0
  - Added `router_priority` to plugin's registrators to allow more precise
      ordering of handlers.
  - Added handlers for raw updates
  - Fixed merging of 'different' routers further
  - Updated comments and documentation for context and plugins

- v4.1.6
  - ^? Fixed merging of 'different' routers
  - Added tests for routers merges

- v4.1.5
  - Fixed `.send_message` with long messages.
  - Fixed `.reply` with non-str argument.
  - Fixed `.resolve_screen_name` for not found users.
  - Fixed `.body` with command and multiline body.

- v4.1.4
  - Fixed bugs in windows

- v4.1.2
  - Improved storage descriptions
  - Improved states processes
  - Removed unused attribute
  - Updated tests and docs

- v4.1.1
  - Updated example plugins
  - Improved error messages

- v4.1.0
  - Fixed case mistake in CommandsRouter
  - Added better API for backends
  - Added example for background actions

- v4.0.0
  - ^ Dramatically changed API
  - Fixed unknown memory leak
  - ^ Added routers for more efficient updates dispatching
  - Added more adequate documentation
  - Added test with 100% coverage
  - ^ Updated examples
  - ^ Updated Makefile
  - ^ Updated codestyle
  - ^ Changed shape of `RequestException`

- v3.2.1
  - Fixed issue with uploading documents to telegram

- v3.2.0
  - ^ Method `upload_doc` for Vkontakte now accepts `type` as
    well as `doctype` keywords.
  - Now graffiti uploads correctly.
  - Updated example "document" and renamed it to "documents".

- v3.1.0
  - ^ `.upload_doc()` now requires filename.
  - Added examples to `example/plugins`.
  - Updated CI configurations.
  - Rebranded engine to library.

- v3.0.0
  - ^ All errors callbacks removed. Now Environment's method "after_process"
    is used. Now when error is happened, bot will **not** write anything to
    the user. Use plugins's `on_after_processed` decorator to add your custom
    behavior.
  - ^ Added `get` method for Environment.
  - ^ Removed Plugin's `register_special` method.
  - ^ Removed all "early"-related code. It was really messy. Everything now
    is works with priority.
  - ^ If your want to make plugin that does something befire other plugins -
    you should split yout plugin into two parts: one with high priority,
    other with normal.
  - ^ Modules now can have multiple plugins with use of `plugins` and `plugin`
    module-level variables.
  - ^ Only one dispose or startup callback can be present on one plugin.
  - ^ Executor's `register*` methods no longer returns decorators.
  - ^ Plugin's arguments like "body", "args" e.t.c. now stored in environment.
  - ^ Renamed Kutana's `storage` to `config`
  - ^ Executors removed entirely, it's functions moved to `Kutana` class.
  - ^ Removed `load_value` method.
  - ^ Renamed manager's `type` to `_type`.
  - ^ Renamed manager's `get_background_coroutines` to `startup`.
  - ^ Added `Plugin.on_message` decorator.
  - Startup now accepts application.
  - Now kutana objects are referred as `app`.
  - Renamed Kutana's "process_update" to "process".
  - Processing is now done inside on Environment.
  - Callbacks storing changed.
