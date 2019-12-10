# Changelog

> Changes to public API is marked as `^`

- v4.0.0
  - ^ Dramatically changed API
  - Fixed unknown memory leak
  - ^ Added routers for more efficient updates dispatching
  - Added more adequate documentation
  - Added test with 100% coverage
  - ^ Updated examples
  - ^ Updated Makefile
  - ^ Updated codestyle

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
